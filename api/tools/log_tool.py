import os
import json
import re
import socket
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, List

try:
    from user_agents import parse as ua_parse
except ImportError:
    ua_parse = None

from nxcore.middleware.logging_manager import logger
from api.model.transaction_model import TransactionDao


def get_server_id():
    return socket.gethostname()


class LogParserTool:

    @classmethod
    def parse_logtime(cls, time_str):
        if not time_str:
            return datetime.now()
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S %z",
            "%a %b %d %H:%M:%S %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
        ):
            try:
                return datetime.strptime(time_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.now()

    @classmethod
    def resolve_status_code(cls, code):
        try:
            c = int(code)
        except (ValueError, TypeError):
            return "PASSED"
        if c == 403:
            return "DENY"
        elif c in [404, 401, 500, 502, 503, 504]:
            return "WARN"
        elif c in [200, 201, 204, 301, 302, 304]:
            return "PASSED"
        return "PASSED"

    @classmethod
    def parse_agent(cls, user_agent_str):
        if not user_agent_str or user_agent_str == "-":
            return {"family": "Unknown", "major": 0, "minor": 0}

        if ua_parse is not None:
            try:
                ua = ua_parse(user_agent_str)
                return {
                    "family": ua.browser.family or "Unknown",
                    "major": (
                        int(ua.browser.version[0])
                        if ua.browser.version and len(ua.browser.version) > 0
                        else 0
                    ),
                    "minor": (
                        int(ua.browser.version[1])
                        if ua.browser.version and len(ua.browser.version) > 1
                        else 0
                    ),
                }
            except Exception:
                pass

        try:
            family = "Unknown"
            major = 0
            minor = 0
            match = re.search(
                r"(Firefox|Chrome|Safari|Edg(?:e)?|OPR|Opera|PostmanRuntime|curl|Python-requests|Wget)/(\d+)(?:\.(\d+))?",
                user_agent_str,
                re.IGNORECASE,
            )
            if match:
                family = match.group(1)
                major = int(match.group(2))
                minor = int(match.group(3)) if match.group(3) else 0
            elif "Mozilla" in user_agent_str:
                family = "Mozilla"
            return {"family": family, "major": major, "minor": minor}
        except Exception:
            return {"family": "Unknown", "major": 0, "minor": 0}

    @classmethod
    def parse_headers(cls, headers_dict):
        if not headers_dict or not isinstance(headers_dict, dict):
            return []
        headers_list = []
        for k, v in headers_dict.items():
            headers_list.append({"name": str(k), "content": str(v)})
        return headers_list

    @classmethod
    def _extract_json_objects(cls, line: str) -> List[Dict[str, Any]]:
        line = line.strip()
        if not line:
            return []
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                return [parsed]
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        pos = 0
        length = len(line)
        results = []
        while pos < length:
            idx = line.find("{", pos)
            if idx == -1:
                break
            try:
                obj, end_pos = decoder.raw_decode(line, idx)
                if isinstance(obj, dict):
                    results.append(obj)
                pos = max(end_pos, idx + 1)
            except json.JSONDecodeError:
                pos = idx + 1
        return results

    @classmethod
    def merge_transactions(cls, service_name, cache):
        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        logger.info(f"Start merge transaction for {service_name}")

        pending_access: Dict[str, tuple[Dict[str, Any], float]] = {}
        pending_audit: Dict[str, tuple[Dict[str, Any], float]] = {}

        while getattr(cur_thread, "active", True):
            time.sleep(2)
            try:
                access_records = []
                audit_records = []

                with cache.lock:
                    if cache.access_log:
                        access_records = list(cache.access_log)
                        cache.access_log.clear()
                    if cache.audit_log:
                        audit_records = list(cache.audit_log)
                        cache.audit_log.clear()

                now = time.time()
                merged_records = []

                # Correlate incoming access records
                for acc in access_records:
                    uid = acc.get("unique_id")
                    if uid:
                        if uid in pending_audit:
                            aud, _ = pending_audit.pop(uid)
                            merged = cls._combine_access_and_audit(
                                acc, aud, service_name
                            )
                            merged_records.append(merged)
                        else:
                            pending_access[uid] = (acc, now)
                    else:
                        if not acc.get("service") or not acc["service"].get("_id"):
                            acc["service"] = {"_id": service_name, "name": service_name}
                        merged_records.append(acc)

                # Correlate incoming audit records
                for aud in audit_records:
                    uid = aud.get("unique_id")
                    if uid:
                        if uid in pending_access:
                            acc, _ = pending_access.pop(uid)
                            merged = cls._combine_access_and_audit(
                                acc, aud, service_name
                            )
                            merged_records.append(merged)
                        else:
                            pending_audit[uid] = (aud, now)
                    else:
                        standalone = cls._audit_to_transaction(aud, service_name)
                        merged_records.append(standalone)

                # Flush pending access records older than 4 seconds
                expired_access_uids = [
                    uid for uid, (_, t) in pending_access.items() if now - t > 4.0
                ]
                for uid in expired_access_uids:
                    acc, _ = pending_access.pop(uid)
                    if not acc.get("service") or not acc["service"].get("_id"):
                        acc["service"] = {"_id": service_name, "name": service_name}
                    merged_records.append(acc)

                # Flush pending audit records older than 4 seconds
                expired_audit_uids = [
                    uid for uid, (_, t) in pending_audit.items() if now - t > 4.0
                ]
                for uid in expired_audit_uids:
                    aud, _ = pending_audit.pop(uid)
                    standalone = cls._audit_to_transaction(aud, service_name)
                    merged_records.append(standalone)

                if merged_records:
                    with TransactionDao() as model:
                        for record in merged_records:
                            try:
                                model.upsert_by_unique_id(record)
                            except Exception as e:
                                logger.error(
                                    f"Error persisting merged transaction: {e}"
                                )
            except Exception as e:
                logger.error(
                    f"Error merging transactions for {service_name}: {e} {traceback.format_exc()}"
                )

        logger.info(f"Merge transaction stopped for {service_name}")

    @classmethod
    def _combine_access_and_audit(
        cls, access: Dict[str, Any], audit: Dict[str, Any], service_name: str = None
    ) -> Dict[str, Any]:
        merged = dict(access)
        if "audit" in audit and audit["audit"]:
            merged["audit"] = audit["audit"]
        if "score" in audit and audit["score"]:
            merged["score"] = max(merged.get("score", 0), audit["score"])

        # Determine action (DENY takes precedence over WARN over PASSED)
        if audit.get("action") == "DENY" or merged.get("action") == "DENY":
            merged["action"] = "DENY"
        elif audit.get("action") == "WARN" or merged.get("action") == "WARN":
            merged["action"] = "WARN"

        # Check status code for blocking
        status_code = merged.get("http", {}).get("response", {}).get("status_code")
        if not status_code and "http" in audit:
            status_code = audit.get("http", {}).get("response", {}).get("status_code")
        if status_code in [403, 406]:
            merged["action"] = "DENY"

        if service_name and (
            not merged.get("service") or not merged["service"].get("_id")
        ):
            merged["service"] = {"_id": service_name, "name": service_name}

        if "http" in audit and audit["http"]:
            aud_http = audit["http"]
            acc_http = merged.get("http", {})
            if "request" in aud_http and aud_http["request"]:
                if "headers" in aud_http["request"] and aud_http["request"]["headers"]:
                    acc_http.setdefault("request", {})["headers"] = aud_http["request"][
                        "headers"
                    ]
                if "method" in aud_http["request"] and not acc_http.get(
                    "request", {}
                ).get("method"):
                    acc_http.setdefault("request", {})["method"] = aud_http["request"][
                        "method"
                    ]
                if "uri" in aud_http["request"] and not acc_http.get("request", {}).get(
                    "uri"
                ):
                    acc_http.setdefault("request", {})["uri"] = aud_http["request"][
                        "uri"
                    ]

            if "response" in aud_http and aud_http["response"]:
                if (
                    "headers" in aud_http["response"]
                    and aud_http["response"]["headers"]
                ):
                    acc_http.setdefault("response", {})["headers"] = aud_http[
                        "response"
                    ]["headers"]
                if "status_code" in aud_http["response"] and not acc_http.get(
                    "response", {}
                ).get("status_code"):
                    acc_http.setdefault("response", {})["status_code"] = aud_http[
                        "response"
                    ]["status_code"]

            merged["http"] = acc_http

        return merged

    @classmethod
    def _audit_to_transaction(
        cls, audit: Dict[str, Any], service_name: str
    ) -> Dict[str, Any]:
        server_id = get_server_id()
        remote_ip = audit.get("source", {}).get("ip", "")
        geo_info = {"ip": remote_ip, "country": "--"}

        status_code = audit.get("http", {}).get("response", {}).get("status_code", 403)
        action = audit.get("action") or cls.resolve_status_code(status_code)

        record = {
            "logtime": audit.get("logtime") or datetime.now(),
            "unique_id": audit.get("unique_id", ""),
            "server_id": audit.get("server_id") or server_id,
            "service": {"_id": service_name, "name": service_name},
            "route_name": "-",
            "upstream": None,
            "sensor": None,
            "action": action,
            "limit_req_status": "",
            "geoip_status": "",
            "rbl_status": "",
            "rate_limit": {},
            "geoip": {},
            "reputation": {},
            "mtls": {},
            "score": audit.get("score", 0),
            "user_agent": {"family": "Unknown", "major": 0, "minor": 0},
            "source": {
                "ip": remote_ip,
                "port": audit.get("source", {}).get("port", 0),
                "geo": geo_info,
            },
            "destination": {
                "ip": audit.get("destination", {}).get("ip", ""),
                "port": audit.get("destination", {}).get("port", 443),
                "host": "",
            },
            "http": audit.get("http", {}),
            "audit": audit.get("audit", {}),
        }
        return record

    @classmethod
    def _parse_and_cache_line(cls, log_type: str, line: str, cache):
        records = []
        try:
            if log_type == "ERROR":
                r = cls.error_log(line)
            elif log_type == "ACCESS":
                r = cls.access_log(line)
            elif log_type == "AUDIT":
                r = cls.audit_log(line)
            else:
                r = None

            if r:
                records = [r] if not isinstance(r, list) else r
        except Exception as e:
            logger.error(f"Error parsing {log_type} line: {e}")

        if records:
            with cache.lock:
                if log_type == "ERROR":
                    cache.error_log.extend(records)
                elif log_type == "ACCESS":
                    cache.access_log.extend(records)
                elif log_type == "AUDIT":
                    cache.audit_log.extend(records)

    @classmethod
    def follow_file(cls, file_path, log_type, cache):
        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        logger.info(f"Starting continuous watcher on {file_path} for {log_type}")

        while getattr(cur_thread, "active", True):
            if not os.path.exists(file_path):
                time.sleep(1)
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    logger.info(f"Opened {file_path} for continuous {log_type} tailing")
                    file.seek(0, 2)
                    buffer = ""
                    last_ino = os.fstat(file.fileno()).st_ino

                    while getattr(cur_thread, "active", True):
                        try:
                            st = os.stat(file_path)
                            if st.st_ino != last_ino or file.tell() > st.st_size:
                                logger.info(
                                    f"File {file_path} rotated or truncated, reopening"
                                )
                                break
                        except Exception:
                            pass

                        chunk = file.readline()
                        if not chunk:
                            time.sleep(0.3)
                            continue

                        if not chunk.endswith("\n"):
                            buffer += chunk
                            time.sleep(0.05)
                            continue

                        line = (buffer + chunk).strip()
                        buffer = ""
                        if not line:
                            continue

                        cls._parse_and_cache_line(log_type, line, cache)

            except Exception as e:
                logger.error(f"Continuous tailing exception on {file_path}: {e}")
                time.sleep(1)

        logger.info(f"Continuous watcher on {file_path} stopped")

    @classmethod
    def error_log(cls, line):
        try:
            return line
        except Exception as e:
            logger.error(f"Error parsing log {e}")

    @classmethod
    def _parse_audit_message_item(cls, m, record: dict) -> dict:
        d = m.get("details", {}) if isinstance(m, dict) else {}
        rule_id = str(d.get("ruleId") or "")
        msg = {
            "text": m.get("message", ""),
            "message": m.get("message", ""),
            "rule_code": rule_id,
            "ruleId": rule_id,
            "match": d.get("match", ""),
            "reference": d.get("reference", ""),
            "data": d.get("data", ""),
            "severity": str(d.get("severity") or ""),
            "file": d.get("file", ""),
            "lineNumber": str(d.get("lineNumber") or ""),
            "tags": d.get("tags", []),
            "ver": d.get("ver", ""),
            "rev": d.get("rev", ""),
            "maturity": str(d.get("maturity") or ""),
            "accuracy": str(d.get("accuracy") or ""),
        }

        if rule_id in ["949110", "959100", "980130", "99"]:
            data_str = str(d.get("data") or m.get("message") or "")
            score_match = re.search(
                r"(?:Total\s*(?:Anomaly\s*)?Score|Score|Matched Data):\s*(\d+)",
                data_str,
                re.IGNORECASE,
            )
            if score_match:
                try:
                    record["score"] = max(
                        record.get("score", 0),
                        int(score_match.group(1)),
                    )
                except (ValueError, TypeError):
                    pass
            elif data_str.isdigit():
                record["score"] = max(record.get("score", 0), int(data_str))
        return msg

    @classmethod
    def _calculate_fallback_score(cls, messages: list) -> int:
        sev_weights = {"2": 5, "3": 4, "4": 3, "5": 2, "1": 2}
        return sum(sev_weights.get(str(m.get("severity") or ""), 0) for m in messages)

    @classmethod
    def _parse_audit_transaction(cls, trn: dict, server_id: str) -> dict:
        trn_server_id = trn.get("server_id") or server_id
        unique_id = trn.get("unique_id") or trn.get("uniqueid")

        record = {
            "logtime": cls.parse_logtime(trn.get("time_stamp")),
            "server_id": trn_server_id,
            "unique_id": unique_id,
            "destination": {
                "ip": trn.get("host_ip", ""),
                "port": trn.get("host_port", 443),
            },
            "source": {
                "ip": trn.get("client_ip", ""),
                "port": trn.get("client_port", 0),
            },
        }

        http = {}
        if "request" in trn:
            request_raw = trn.pop("request")
            http["version"] = str(request_raw.get("http_version", "1.1"))
            http["request"] = {
                "method": request_raw.get("method", "GET"),
                "uri": request_raw.get("uri", ""),
                "headers": cls.parse_headers(request_raw.get("headers", {})),
            }

        action = "PASSED"
        if "response" in trn:
            response_raw = trn.pop("response")
            status_code = response_raw.get("http_code", 200)
            http["response"] = {
                "status_code": status_code,
                "headers": cls.parse_headers(response_raw.get("headers", {})),
            }
            action = cls.resolve_status_code(status_code)
        record.update({"http": http, "action": action})

        audit = {}
        if "producer" in trn:
            producer_raw = trn.pop("producer")
            audit.update(
                {
                    "engine": producer_raw.get("modsecurity", ""),
                    "connector": producer_raw.get("connector", ""),
                    "mode": producer_raw.get("secrules_engine", ""),
                    "components": producer_raw.get("components", []),
                }
            )

        if "messages" in trn:
            messages_raw = trn.pop("messages") or []
            messages = [cls._parse_audit_message_item(m, record) for m in messages_raw]
            audit["messages"] = messages

            if "score" not in record and messages:
                record["score"] = cls._calculate_fallback_score(messages)

            if record.get("action") != "DENY":
                if any(str(m.get("severity") or "") in ["2", "3"] for m in messages):
                    record["action"] = "DENY"

        record.update({"audit": audit})
        return record

    @classmethod
    def audit_log(cls, line):
        dtos = cls._extract_json_objects(line)
        if not dtos:
            return None

        server_id = get_server_id()
        records = []
        for dto in dtos:
            try:
                if "transaction" in dto:
                    record = cls._parse_audit_transaction(
                        dto.pop("transaction"), server_id
                    )
                    records.append(record)
            except Exception as e:
                logger.error(f"Error parsing audit log item: {e}")
        return records if records else None

    @classmethod
    def access_log(cls, line):
        dtos = cls._extract_json_objects(line)
        if not dtos:
            return None

        server_id = get_server_id()
        records = []
        for dto in dtos:
            try:
                remote_ip = dto.get("remote_addr", "")
                country_code = "--"
                if isinstance(dto.get("geoip"), dict):
                    country_code = dto["geoip"].get("country_code") or "--"
                elif isinstance(dto.get("geoip"), str):
                    country_code = dto.get("geoip") or "--"

                if country_code in ["None", "null", ""]:
                    country_code = "--"

                geo_info = {
                    "ip": remote_ip,
                    "country": country_code,
                }

                status_code = dto.get("status", 200)
                service_val = dto.get("service") or dto.get("service_id")
                service_obj = (
                    {"_id": service_val, "name": service_val} if service_val else None
                )

                route_name = dto.get("route") or dto.get("route_name") or "-"
                upstream_val = dto.get("upstream")
                if isinstance(upstream_val, dict):
                    upstream_obj = upstream_val
                elif upstream_val and upstream_val != "-":
                    upstream_obj = {"name": upstream_val, "_id": upstream_val}
                else:
                    upstream_obj = None

                sensor_val = dto.get("sensor") or dto.get("sensor_id")
                if isinstance(sensor_val, dict):
                    sensor_obj = sensor_val
                elif sensor_val and sensor_val != "-":
                    sensor_obj = {"name": sensor_val, "_id": sensor_val}
                else:
                    sensor_obj = None

                rate_limit_dto = dto.get("rate_limit") or {}
                limit_req_status = (
                    rate_limit_dto.get("action")
                    if isinstance(rate_limit_dto, dict)
                    else (dto.get("limit_req_status") or "")
                )

                geoip_dto = dto.get("geoip") or {}
                geoip_status = (
                    geoip_dto.get("action")
                    if isinstance(geoip_dto, dict)
                    else (dto.get("geoip_status") or "")
                )

                reputation_dto = dto.get("reputation") or {}
                rbl_status = (
                    reputation_dto.get("action")
                    if isinstance(reputation_dto, dict)
                    else (dto.get("rbl_status") or "")
                )
                score = (
                    reputation_dto.get("score", 0)
                    if isinstance(reputation_dto, dict)
                    else 0
                )

                host_header = dto.get("host", "")
                host_ip = host_header.split(":")[0] if host_header else ""

                req_method = dto.get("method")
                req_uri = ""
                if dto.get("request_line"):
                    req_parts = dto["request_line"].strip().split()
                    if req_parts:
                        if not req_method:
                            req_method = req_parts[0]
                        if len(req_parts) > 1:
                            req_uri = req_parts[1]
                if not req_method:
                    req_method = "GET"

                record = {
                    "logtime": cls.parse_logtime(dto.get("time")),
                    "unique_id": dto.get("uniqueid") or dto.get("unique_id"),
                    "server_id": dto.get("server_id") or server_id,
                    "service": service_obj,
                    "route_name": route_name,
                    "upstream": upstream_obj,
                    "sensor": sensor_obj,
                    "action": cls.resolve_status_code(status_code),
                    "limit_req_status": limit_req_status,
                    "geoip_status": geoip_status,
                    "rbl_status": rbl_status,
                    "rate_limit": (
                        rate_limit_dto if isinstance(rate_limit_dto, dict) else {}
                    ),
                    "geoip": geoip_dto if isinstance(geoip_dto, dict) else {},
                    "reputation": (
                        reputation_dto if isinstance(reputation_dto, dict) else {}
                    ),
                    "ipxa": dto.get("ipxa", ""),
                    "mtls": (
                        dto.get("mtls", {}) if isinstance(dto.get("mtls"), dict) else {}
                    ),
                    "score": score,
                    "user_agent": cls.parse_agent(dto.get("user_agent", "")),
                    "source": {
                        "ip": remote_ip,
                        "port": dto.get("remote_port", 0),
                        "geo": geo_info,
                    },
                    "destination": {
                        "ip": host_ip,
                        "port": dto.get("server_port", 443),
                        "host": host_header,
                    },
                    "http": {
                        "duration": dto.get("duration", 0.0),
                        "uht": dto.get("uht", 0.0),
                        "urt": dto.get("urt", 0.0),
                        "referer": dto.get("referer", ""),
                        "request_line": dto.get("request_line", ""),
                        "request": {
                            "method": req_method,
                            "uri": req_uri,
                            "bytes": dto.get("bytes_in", 0),
                        },
                        "response": {
                            "status_code": status_code,
                            "bytes": dto.get("bytes_out", 0),
                        },
                    },
                }
                records.append(record)
            except Exception as e:
                logger.error(f"Error parsing access log item: {e}")
        return records if records else None
