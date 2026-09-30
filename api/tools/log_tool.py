import json
import os
import threading
import time
import traceback
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from nxcore.middleware.logging_manager import logger

from api.repository.config_repository import ConfigDao
from api.repository.transaction_repository import TransactionDao
from api.repository.upstream_repository import NodeStatusDao
from api.services.elasticsearch_service import ElasticsearchService
from api.tools.http_parse_tool import (
    parse_agent as _parse_agent,
    parse_headers as _parse_headers,
    resolve_status_code as _resolve_status_code,
)
from api.tools.type_parse_tool import (
    parse_logtime as _parse_logtime,
    to_float as _to_float,
    to_int as _to_int,
)
from config import (
    SCORE_REGEX,
    SEVERITY_WEIGHTS,
    SERVER_ID,
    TZ,
)

class LogParserTool:
    """High-performance log parsing, normalization, file watching, and correlation tool."""

    # =========================================================================
    # 1. Parsing and Normalization
    # =========================================================================

    @classmethod
    def error_log(cls, line: str):
        """Processes raw error log lines."""
        return line

    @classmethod
    def access_log(cls, line: str) -> Optional[Dict[str, Any]]:
        """Parses a line containing Nginx access log JSON."""
        line = line.strip()
        if not line:
            return None
        try:
            dto = json.loads(line)
        except Exception:
            return None
        if not isinstance(dto, dict):
            return None

        try:
            remote_ip = dto.get("remote_addr", "")
            geoip_dto = dto.get("geoip") or {}
            country_code = geoip_dto.get("country_code") or "--"
            if country_code in ("None", "null", ""):
                country_code = "--"

            geo_info = {
                "ip": remote_ip,
                "country": country_code,
            }

            status_code = _to_int(dto.get("status", 200), 200)

            service_val = dto.get("service")
            service_obj = (
                {"_id": str(service_val), "name": str(service_val)}
                if service_val and service_val != "-"
                else None
            )

            route_name = dto.get("route") or "-"

            upstream_val = dto.get("upstream")
            upstream_obj = (
                upstream_val
                if isinstance(upstream_val, dict) and upstream_val.get("name") not in (None, "-")
                else None
            )

            sensor_val = dto.get("sensor")
            sensor_obj = (
                sensor_val
                if isinstance(sensor_val, dict) and sensor_val.get("name") not in (None, "-")
                else None
            )

            rate_limit_dto = dto.get("rate_limit") or {}
            limit_req_status = rate_limit_dto.get("action") or ""
            geoip_status = geoip_dto.get("action") or ""

            reputation_dto = dto.get("reputation") or {}
            rbl_status = reputation_dto.get("action") or ""
            score = _to_int(reputation_dto.get("score", 0))

            host_header = dto.get("host", "")
            host_ip = host_header.split(":")[0] if host_header else ""

            req_method = dto.get("method") or "GET"
            req_uri = ""
            if dto.get("request_line"):
                req_parts = dto["request_line"].strip().split()
                if len(req_parts) > 1:
                    req_uri = req_parts[1]
                if not dto.get("method") and req_parts:
                    req_method = req_parts[0]

            return {
                "logtime": _parse_logtime(dto.get("time")),
                "unique_id": dto.get("uniqueid") or dto.get("unique_id"),
                "server_id": dto.get("server_id") or SERVER_ID,
                "service": service_obj,
                "route_name": route_name,
                "upstream": upstream_obj,
                "sensor": sensor_obj,
                "action": _resolve_status_code(status_code),
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
                "user_agent": _parse_agent(dto.get("user_agent", "")),
                "source": {
                    "ip": remote_ip,
                    "port": _to_int(dto.get("remote_port", 0)),
                    "geo": geo_info,
                },
                "destination": {
                    "ip": host_ip,
                    "port": _to_int(dto.get("server_port", 443), 443),
                    "host": host_header,
                },
                "http": {
                    "duration": _to_float(dto.get("duration", 0.0)),
                    "uht": _to_float(dto.get("uht", 0.0)),
                    "urt": _to_float(dto.get("urt", 0.0)),
                    "referer": dto.get("referer", ""),
                    "request_line": dto.get("request_line", ""),
                    "request": {
                        "method": req_method,
                        "uri": req_uri,
                        "bytes": _to_int(dto.get("bytes_in", 0)),
                    },
                    "response": {
                        "status_code": status_code,
                        "bytes": _to_int(dto.get("bytes_out", 0)),
                    },
                },
            }
        except Exception as e:
            logger.error(f"Error parsing access log item: {e}")
            return None

    @classmethod
    def audit_log(cls, line: str) -> Optional[Dict[str, Any]]:
        """Parses a line containing ModSecurity audit log JSON."""
        line = line.strip()
        if not line:
            return None
        try:
            dto = json.loads(line)
        except Exception:
            return None
        if not isinstance(dto, dict) or "transaction" not in dto:
            return None

        try:
            trn = dto.pop("transaction")
            trn_server_id = trn.get("server_id") or SERVER_ID
            unique_id = trn.get("unique_id") or trn.get("uniqueid")

            record = {
                "logtime": _parse_logtime(trn.get("time_stamp")),
                "server_id": trn_server_id,
                "unique_id": unique_id,
                "destination": {
                    "ip": trn.get("host_ip", ""),
                    "port": _to_int(trn.get("host_port", 443), 443),
                },
                "source": {
                    "ip": trn.get("client_ip", ""),
                    "port": _to_int(trn.get("client_port", 0), 0),
                },
            }

            http = {}
            if "request" in trn:
                request_raw = trn.pop("request")
                http["version"] = str(request_raw.get("http_version", "1.1"))
                http["request"] = {
                    "method": str(request_raw.get("method", "GET")),
                    "uri": str(request_raw.get("uri", "")),
                    "headers": _parse_headers(request_raw.get("headers", {})),
                }

            action = "allowed"
            if "response" in trn:
                response_raw = trn.pop("response")
                status_code = _to_int(response_raw.get("http_code", 200), 200)
                http["response"] = {
                    "status_code": status_code,
                    "headers": _parse_headers(response_raw.get("headers", {})),
                }
                action = _resolve_status_code(status_code)
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

                    if rule_id in ("949110", "959100", "980130", "99"):
                        data_str = str(d.get("data") or m.get("message") or "")
                        score_match = SCORE_REGEX.search(data_str)
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

                if "score" not in record and messages:
                    record["score"] = sum(
                        SEVERITY_WEIGHTS.get(str(m.get("severity") or ""), 0)
                        for m in messages
                    )

                if str(record.get("action") or "").lower() not in (
                    "blocked",
                    "deny",
                    "block",
                ):
                    if any(
                        str(m.get("severity") or "") in ("2", "3") for m in messages
                    ):
                        record["action"] = "blocked"

            record.update({"audit": audit})
            return record
        except Exception as e:
            logger.error(f"Error parsing audit log item: {e}")
            return None

    # =========================================================================
    # 2. File Ingestion and Tailing
    # =========================================================================

    @classmethod
    def follow_file(cls, file_path: str, log_type: str, cache):
        """Continuously tails a log file with rotation draining and line batching."""
        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        logger.info(f"Starting continuous watcher on {file_path} for {log_type}")
        initial_file_existed = os.path.exists(file_path)
        initial_open = True

        while getattr(cur_thread, "active", True):
            if not os.path.exists(file_path):
                time.sleep(1)
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                    logger.info(f"Opened {file_path} for continuous {log_type} tailing")
                    if initial_open:
                        if initial_file_existed:
                            file.seek(0, os.SEEK_END)
                        initial_open = False
                    buffer = ""
                    last_ino = os.fstat(file.fileno()).st_ino
                    last_check = time.time()

                    while getattr(cur_thread, "active", True):
                        raw_lines = file.readlines(65536)
                        if raw_lines:
                            if buffer:
                                raw_lines[0] = buffer + raw_lines[0]
                                buffer = ""
                            if not raw_lines[-1].endswith("\n"):
                                buffer = raw_lines.pop()
                            batch = [l.strip() for l in raw_lines if l.strip()]
                            if batch:
                                cls._parse_and_cache_lines(log_type, batch, cache)
                            continue

                        now = time.time()
                        if now - last_check >= 0.5:
                            last_check = now
                            try:
                                st = os.stat(file_path)
                                if st.st_ino != last_ino:
                                    logger.info(
                                        f"File {file_path} rotated, draining remaining content"
                                    )
                                    remaining = file.read().splitlines()
                                    if remaining:
                                        cls._parse_and_cache_lines(
                                            log_type,
                                            [l.strip() for l in remaining if l.strip()],
                                            cache,
                                        )
                                    break
                                elif file.tell() > st.st_size:
                                    logger.info(
                                        f"File {file_path} truncated, resetting read position"
                                    )
                                    file.seek(0, 0)
                                    buffer = ""
                            except Exception:
                                pass

                        time.sleep(0.2)

            except Exception as e:
                logger.error(f"Continuous tailing exception on {file_path}: {e}")
                time.sleep(1)

        logger.info(f"Continuous watcher on {file_path} stopped")

    @classmethod
    def _parse_and_cache_lines(cls, log_type: str, lines: List[str], cache):
        """Parses a batch of lines and updates the shared memory cache atomically."""
        parser = {
            "ACCESS": cls.access_log,
            "AUDIT": cls.audit_log,
            "ERROR": cls.error_log,
        }.get(log_type)

        if not parser:
            return

        all_records = []
        for line in lines:
            try:
                r = parser(line)
                if r:
                    if isinstance(r, list):
                        all_records.extend(r)
                    else:
                        all_records.append(r)
            except Exception as e:
                logger.error(f"Error parsing {log_type} line: {e}")

        if all_records:
            if hasattr(cache, "push_many"):
                cache.push_many(log_type, all_records)
            else:
                with cache.lock:
                    target = getattr(cache, f"{log_type.lower()}_log", None)
                    if target is not None:
                        target.extend(all_records)

    # =========================================================================
    # 3. Correlation and Merging
    # =========================================================================

    @classmethod
    def merge_transactions(cls, service_name: str, cache):
        """Worker thread correlating access and audit logs by unique_id into transactions."""
        cur_thread = threading.current_thread()
        setattr(cur_thread, "active", True)
        logger.info(f"Start merge transaction for {service_name}")

        default_service = cls._get_service_info(service_name)
        pending_access: Dict[str, tuple[Dict[str, Any], int]] = {}
        pending_audit: Dict[str, tuple[Dict[str, Any], int]] = {}
        logging_mode, logging_conf = "local", None
        last_config_check = 0.0

        while getattr(cur_thread, "active", True):
            now = time.time()
            if now - last_config_check >= 2.0:
                logging_mode, logging_conf = cls._get_logging_config()
                last_config_check = now

            access_records = cache.drain("ACCESS", max_items=2500)
            audit_records = cache.drain("AUDIT", max_items=2500)

            try:
                merged_records = []
                if access_records or audit_records:
                    logger.debug(
                        f"[{service_name}] Ingesting Access: {len(access_records)}, Audit: {len(audit_records)}"
                    )

                cls._correlate(
                    access_records,
                    audit_records,
                    pending_access,
                    pending_audit,
                    merged_records,
                    default_service=default_service,
                    max_retries=30,
                )

                if merged_records:
                    cls._flush_merged(
                        merged_records, service_name, logging_mode, logging_conf
                    )

            except Exception as e:
                logger.error(
                    f"Error merging transactions for {service_name}: {e} {traceback.format_exc()}"
                )

            time.sleep(0.25 if (access_records or audit_records) else 1.5)

        # Graceful final flush upon thread exit
        try:
            final_records = (
                [cls._combine(acc, None, default_service) for acc in cache.drain_all("ACCESS")]
                + [cls._combine(None, aud, default_service) for aud in cache.drain_all("AUDIT")]
                + [cls._combine(acc, None, default_service) for acc, _ in pending_access.values()]
                + [cls._combine(None, aud, default_service) for aud, _ in pending_audit.values()]
            )
            pending_access.clear()
            pending_audit.clear()

            if final_records:
                cls._flush_merged(
                    final_records, service_name, logging_mode, logging_conf
                )
        except Exception as e:
            logger.error(
                f"Error during final transaction flush for {service_name}: {e}"
            )

        logger.info(f"Merge transaction stopped for {service_name}")

    @classmethod
    def _correlate(
        cls,
        access_records: List[Dict[str, Any]],
        audit_records: List[Dict[str, Any]],
        pending_access: Dict[str, tuple[Dict[str, Any], int]],
        pending_audit: Dict[str, tuple[Dict[str, Any], int]],
        merged_records: List[Dict[str, Any]],
        default_service: Optional[Dict[str, str]] = None,
        max_retries: int = 30,
    ):
        """Correlates access and audit logs, increments retry counter, and flushes items exceeding max_retries."""
        for acc in access_records:
            uid = acc.get("unique_id")
            if not uid:
                merged_records.append(cls._combine(acc, None, default_service))
            elif uid in pending_audit:
                aud, _ = pending_audit.pop(uid)
                merged_records.append(cls._combine(acc, aud, default_service))
            else:
                pending_access[uid] = (acc, 0)

        for aud in audit_records:
            uid = aud.get("unique_id")
            if not uid:
                merged_records.append(cls._combine(None, aud, default_service))
            elif uid in pending_access:
                acc, _ = pending_access.pop(uid)
                merged_records.append(cls._combine(acc, aud, default_service))
            else:
                pending_audit[uid] = (aud, 0)

        for pending_dict, is_access in ((pending_access, True), (pending_audit, False)):
            for uid, (rec, count) in list(pending_dict.items()):
                new_count = count + 1
                if new_count > max_retries:
                    pending_dict.pop(uid)
                    merged_records.append(
                        cls._combine(rec, None, default_service)
                        if is_access
                        else cls._combine(None, rec, default_service)
                    )
                else:
                    pending_dict[uid] = (rec, new_count)

    @classmethod
    def _combine(
        cls,
        access: Optional[Dict[str, Any]],
        audit: Optional[Dict[str, Any]],
        default_service: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Combines correlated access and audit records, or formats standalone logs into transactions."""
        if not access:
            if not audit:
                return {}
            remote_ip = audit.get("source", {}).get("ip", "")
            status_code = _to_int(
                audit.get("http", {}).get("response", {}).get("status_code"), 403
            )
            raw_action = str(audit.get("action") or "").lower()
            if raw_action in ("deny", "block", "blocked"):
                action = "blocked"
            elif raw_action in ("warn", "warning"):
                action = "warn"
            elif raw_action in ("allow", "allowed", "pass", "passed"):
                action = "allowed"
            else:
                action = _resolve_status_code(status_code)

            return {
                "logtime": audit.get("logtime") or datetime.now(),
                "unique_id": audit.get("unique_id", ""),
                "server_id": audit.get("server_id") or SERVER_ID,
                "service": default_service,
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
                "score": _to_int(audit.get("score", 0)),
                "user_agent": {"family": "Unknown", "major": 0, "minor": 0},
                "source": {
                    "ip": remote_ip,
                    "port": _to_int(audit.get("source", {}).get("port", 0)),
                    "geo": {"ip": remote_ip, "country": "--"},
                },
                "destination": {
                    "ip": audit.get("destination", {}).get("ip", ""),
                    "port": _to_int(audit.get("destination", {}).get("port", 443), 443),
                    "host": "",
                },
                "http": audit.get("http", {}),
                "audit": audit.get("audit", {}),
            }

        merged = dict(access)
        if not merged.get("service") or not merged["service"].get("name"):
            merged["service"] = default_service

        if not audit:
            return merged

        if audit.get("audit"):
            merged["audit"] = audit["audit"]
        if audit.get("score"):
            merged["score"] = max(merged.get("score", 0), audit["score"])

        audit_act = str(audit.get("action") or "").lower()
        merged_act = str(merged.get("action") or "").lower()
        if audit_act in ("deny", "blocked", "block") or merged_act in (
            "deny",
            "blocked",
            "block",
        ):
            merged["action"] = "blocked"
        elif audit_act in ("warn", "warning") or merged_act in ("warn", "warning"):
            merged["action"] = "warn"

        status_code = _to_int(
            merged.get("http", {}).get("response", {}).get("status_code"), 0
        ) or _to_int(
            audit.get("http", {}).get("response", {}).get("status_code"), 0
        )
        if status_code in (403, 406):
            merged["action"] = "blocked"

        if audit.get("http"):
            aud_http = audit["http"]
            acc_http = merged.setdefault("http", {})
            aud_req = aud_http.get("request") or {}
            if aud_req:
                acc_req = acc_http.setdefault("request", {})
                if aud_req.get("headers"):
                    acc_req["headers"] = _parse_headers(aud_req["headers"])
                if aud_req.get("method") and not acc_req.get("method"):
                    acc_req["method"] = aud_req["method"]
                if aud_req.get("uri") and not acc_req.get("uri"):
                    acc_req["uri"] = aud_req["uri"]

            aud_resp = aud_http.get("response") or {}
            if aud_resp:
                acc_resp = acc_http.setdefault("response", {})
                if aud_resp.get("headers"):
                    acc_resp["headers"] = _parse_headers(aud_resp["headers"])
                if aud_resp.get("status_code") and not acc_resp.get("status_code"):
                    acc_resp["status_code"] = _to_int(aud_resp["status_code"], 200)

        return merged

    @classmethod
    def _flush_merged(
        cls,
        records: List[Dict[str, Any]],
        service_name: str,
        mode: str,
        conf: Optional[Dict[str, Any]],
    ):
        """Flushes correlated transaction records to DuckDB or Elasticsearch."""
        if not records:
            return
        logger.info(
            f"[{service_name}] Flushing {len(records)} merged transactions to {mode}"
        )
        if mode in ["elasticsearch"]:
            with ElasticsearchService(conf or {}) as es_service:
                es_service.persist_many(records)
        else:
            with TransactionDao() as model:
                for record in records:
                    try:
                        model.upsert_by_unique_id(record)
                    except Exception as e:
                        logger.error(f"Error persisting merged transaction: {e}")
        logger.debug(
            f"Processed {len(records)} merged transactions for {service_name} (mode: {mode})"
        )

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_service_info(service_name: str) -> Dict[str, str]:
        """Resolves raw service identifier to sanitized service metadata."""
        clean_name = (
            service_name.rsplit("_", 1)[0]
            if ("_" in service_name and service_name.rsplit("_", 1)[1].isdigit())
            else service_name
        )
        return {"_id": service_name, "name": clean_name}

    @classmethod
    def _get_logging_config(cls) -> tuple[str, Optional[Dict[str, Any]]]:
        """Fetches active logging mode and configuration."""
        try:
            with ConfigDao() as config_dao:
                active = config_dao.get_active()
                if active and isinstance(active, dict):
                    logging_conf = active.get("logging") or {}
                    return logging_conf.get("mode", "local"), logging_conf
        except Exception as e:
            logger.debug(f"Error reading logging config: {e}")
        return "local", None

    # =========================================================================
    # 4. Maintenance
    # =========================================================================

    @classmethod
    def clean(cls):
        """Purges expired node statuses and transaction records according to config."""
        now = datetime.now(TZ)
        try:
            with NodeStatusDao() as node_dao, TransactionDao() as trn_dao, ConfigDao() as config_dao:
                node_dao.purge_before_date(now - timedelta(hours=1))
                active = config_dao.get_active()
                purge_config = (active.get("purge") or {}) if active else {}
                if purge_config.get("enabled"):
                    purge_after = _to_int(purge_config.get("purge_after", 30), 30)
                    t_purged = trn_dao.purge_before_date(
                        now - timedelta(days=purge_after)
                    )
                    if t_purged > 0:
                        logger.info(f"Purged {t_purged} transactions")
        except Exception as e:
            logger.error(f"Error during log cleaning / purge: {e}")
