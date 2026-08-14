from api.services.ipxa_services import IPXAService
import json
import re
import threading
import time
import traceback
from datetime import datetime
import requests
from ua_parser import user_agent_parser

from nxcore.middleware.logging_manager import logger

from api.model.config_model import ConfigDao
from nxcore.common_utils import deep_merge, get_server_id
from api.model.transaction_model import TransactionDao
import config as env_config


class LogParserTool:

    telemetry = {
        "net_recv": 0.0,
        "net_send": 0.0,
        "req_total": 0.0,
        "c_interval": 0,
    }

    @classmethod
    def parse_headers(cls, dto):
        headers = []
        if isinstance(dto, dict):
            for key, val in dto.items():
                if key not in ["Authorization"]:
                    headers.append({"name": key, "content": str(val)})
        elif isinstance(dto, list):
            return dto
        return headers

    @classmethod
    def parse_agent(cls, user_agent):
        if not user_agent or not isinstance(user_agent, str):
            return {"family": "Other", "major": "0", "minor": "0"}
        try:
            r = user_agent_parser.Parse(user_agent)
            ua = r.get("user_agent", {})
            return {
                "family": ua.get("family") or "Other",
                "major": str(ua.get("major") or "0"),
                "minor": str(ua.get("minor") or "0"),
            }
        except Exception:
            return {"family": "Other", "major": "0", "minor": "0"}

    @classmethod
    def parse_logtime(cls, val):
        if not val:
            return datetime.now(env_config.TZ)
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=env_config.TZ)
            return val.astimezone(env_config.TZ)

        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d/%b/%Y:%H:%M:%S %z",
            "%d/%b/%Y:%H:%M:%S",
            "%a %b %d %H:%M:%S %Y",
        ):
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=env_config.TZ)
                return dt.astimezone(env_config.TZ)
            except (ValueError, TypeError):
                continue
        try:
            return datetime.fromisoformat(val).astimezone(env_config.TZ)
        except Exception:
            return datetime.now(env_config.TZ)

    @classmethod
    def resolve_status_code(cls, code):
        status_map = {503: "REJECTED", 429: "REJECTED", 403: "DENY"}
        if code is not None:
            try:
                c = int(code)
                if c in status_map:
                    return status_map[c]
                elif c < 400:
                    return "PASSED"
                elif c >= 400:
                    return "WARN"
            except (ValueError, TypeError):
                pass
        return "UNKNOWN"

    @classmethod
    def send_telemetry(cls, t):
        try:
            conf = ConfigDao().get_active()
            if env_config.TELEMETRY_ENABLE and conf:
                t.update({"version": env_config.APP_VERSION})
                t.update({"interval": env_config.TELEMETRY_INTERVAL})
                t.update({"cluster_id": conf.get("cluster_id")})
                t.update({"server_id": get_server_id()})
                t.update(
                    {
                        "logtime": datetime.now(env_config.TZ).strftime(
                            env_config.DATETIME_FMT
                        )
                    }
                )
                env_config.API_HEADERS.update({"Content-Type": "application/json"})
                response = requests.post(
                    f"{env_config.TELEMETRY_URL}/api/usage",
                    json=t,
                    headers=env_config.API_HEADERS,
                    timeout=10,
                )
                if response.status_code not in [200, 201]:
                    logger.warn(f"[{response.status_code}]:{response.text}")
        except Exception as e:
            logger.error(f"Failed to send telemetry, {e}")

    @classmethod
    def merge_transactions(cls, cache, tag):
        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        while getattr(cur_thread, "active", True):
            try:
                with cache.lock:
                    if cache.access_log or cache.audit_log:
                        st_in = [
                            len(cache.audit_log),
                            len(cache.error_log),
                            len(cache.access_log),
                        ]
                        with TransactionDao() as model:
                            for audit in cache.audit_log:
                                for log in cache.access_log:
                                    if (
                                        log.get("unique_id")
                                        and log.get("unique_id") == audit.get("unique_id")
                                    ):
                                        merged = deep_merge(log, audit)
                                        merged.update({"archived": False})
                                        log.update({"flushed": True})
                                        audit.update({"flushed": True})

                                        bytes_send = (
                                            merged.get("http", {})
                                            .get("response", {})
                                            .get("bytes", 0)
                                            or 0
                                        )
                                        bytes_recv = (
                                            merged.get("http", {})
                                            .get("request", {})
                                            .get("bytes", 0)
                                            or 0
                                        )
                                        cls.telemetry["net_send"] += bytes_send / 1048576.0
                                        cls.telemetry["net_recv"] += bytes_recv / 1048576.0
                                        model.persist(merged)
                                        break

                            for log_item in cache.access_log:
                                if "flushed" not in log_item:
                                    merged = log_item.copy()
                                    merged.update({"archived": False})
                                    bytes_send = (
                                        merged.get("http", {})
                                        .get("response", {})
                                        .get("bytes", 0)
                                        or 0
                                    )
                                    bytes_recv = (
                                        merged.get("http", {})
                                        .get("request", {})
                                        .get("bytes", 0)
                                        or 0
                                    )
                                    cls.telemetry["net_send"] += bytes_send / 1048576.0
                                    cls.telemetry["net_recv"] += bytes_recv / 1048576.0
                                    model.persist(merged)

                            cls.telemetry["req_total"] += len(cache.access_log) / 1000.0  # K requests
                            cache.access_log = []
                            cache.audit_log = [a for a in cache.audit_log if "flushed" not in a]
                            cache.error_log = []

                            cls.telemetry["c_interval"] += 1
                            if cls.telemetry["c_interval"] >= env_config.TELEMETRY_INTERVAL:
                                cls.send_telemetry(cls.telemetry.copy())
                                cls.telemetry = {
                                    "net_recv": 0.0,
                                    "net_send": 0.0,
                                    "req_total": 0.0,
                                    "c_interval": 0,
                                }

                            logger.debug(
                                f"[{tag}] - audit[{len(cache.audit_log)}/{st_in[0]}] error[{len(cache.error_log)}/{st_in[1]}] access[{len(cache.access_log)}/{st_in[2]}]"
                            )
            except Exception as e:
                logger.error(f"Error merging transactions for {tag}: {e}")

            time.sleep(2)
        logger.debug(f"merge_transactions shutdown for {tag}")

    @classmethod
    def follow_file(cls, cache, file_path, log_type):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                pass
        except Exception:
            pass

        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                logger.debug(f"Following {file_path} for {log_type}")
                file.seek(0, 2)
                while getattr(cur_thread, "active", True):
                    line = file.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    t = None
                    if log_type == "ERROR":
                        t = cls.error_log(line)
                    elif log_type == "ACCESS":
                        t = cls.access_log(line)
                    elif log_type == "AUDIT":
                        t = cls.audit_log(line)
                    if t:
                        with cache.lock:
                            if log_type == "ERROR":
                                cache.error_log.append(t)
                            elif log_type == "ACCESS":
                                cache.access_log.append(t)
                            elif log_type == "AUDIT":
                                cache.audit_log.append(t)
                logger.info(f"{file_path} shutdown")

        except Exception as e:
            logger.error(f"Read file error {file_path} {e}, retry")

    @classmethod
    def error_log(cls, line):
        try:
            return line
        except Exception as e:
            logger.error(f"Error parsing log {e}")

    @classmethod
    def audit_log(cls, line):
        server_id = get_server_id()
        try:
            dto = json.loads(line)
            if "transaction" in dto:
                trn = dto.pop("transaction")
                trn_server_id = trn.get("server_id") or server_id
                unique_id = trn.get("unique_id") or trn.get("uniqueid")

                record = {
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
                    http.update(
                        {
                            "version": str(request_raw.get("http_version", "1.1")),
                        }
                    )
                    request = {
                        "method": request_raw.get("method", "GET"),
                        "uri": request_raw.get("uri", ""),
                        "headers": cls.parse_headers(request_raw.get("headers", {})),
                    }
                    http.update({"request": request})

                if "response" in trn:
                    response_raw = trn.pop("response")
                    response = {
                        "status_code": response_raw.get("http_code", 200),
                        "headers": cls.parse_headers(response_raw.get("headers", {})),
                    }
                    record.update(
                        {"action": cls.resolve_status_code(response_raw.get("http_code"))}
                    )
                    http.update({"response": response})
                record.update({"http": http})

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
                    messages = []
                    for m in messages_raw:
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

                        # Extract anomaly score if present
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
                                record["score"] = max(
                                    record.get("score", 0), int(data_str)
                                )

                        messages.append(msg)
                    audit["messages"] = messages
                record.update({"audit": audit})
                return record
        except Exception as e:
            logger.error(f"Error parsing audit log {e} {traceback.format_exc()}")

    @classmethod
    def access_log(cls, line):
        server_id = get_server_id()
        try:
            dto = json.loads(line)
            remote_ip = dto.get("remote_addr", "")
            geo_info = IPXAService.geo_info(remote_ip)
            if not geo_info or not geo_info.get("country"):
                country_code = (
                    dto.get("geoip", {}).get("country_code")
                    if isinstance(dto.get("geoip"), dict)
                    else None
                )
                if country_code and country_code != "--":
                    geo_info = geo_info or {}
                    geo_info["country"] = country_code

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
                "rate_limit": rate_limit_dto if isinstance(rate_limit_dto, dict) else {},
                "geoip": geoip_dto if isinstance(geoip_dto, dict) else {},
                "reputation": (
                    reputation_dto if isinstance(reputation_dto, dict) else {}
                ),
                "ipxa": dto.get("ipxa", ""),
                "mtls": dto.get("mtls", {}) if isinstance(dto.get("mtls"), dict) else {},
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
                        "method": dto.get("method", "GET"),
                        "bytes": dto.get("bytes_in", 0),
                    },
                    "response": {
                        "status_code": status_code,
                        "bytes": dto.get("bytes_out", 0),
                    },
                },
            }
            return record
        except Exception:
            logger.error(f"Error parsing access log: {line} {traceback.format_exc()}")
