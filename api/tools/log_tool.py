import json
import threading
import time
import traceback
from datetime import datetime
import requests
from ua_parser import user_agent_parser

from nxcore.middleware.logging import logger

from api.repository.config_model import ConfigDao
from nxcore.common_utils import deep_merge, get_server_id
from api.repository.transaction_model import TransactionDao
from api.tools.feed_service import SecurityFeedService
import config as env_config


class LogParserTool:

    telemetry = {
        "net_recv": 0,
        "net_send": 0,
        "req_total": 0,
        "c_interval": 0,
    }

    @classmethod
    def parse_headers(cls, dto):
        headers = []
        for key, val in dto.items():
            if key not in ["Authorization"]:
                headers.append({"name": key, "content": val})
        return headers

    @classmethod
    def parse_agent(cls, user_agent):
        r = user_agent_parser.Parse(user_agent)
        return {
            "family": r["user_agent"]["family"],
            "major": r["user_agent"]["major"],
            "minor": r["user_agent"]["minor"],
        }

    @classmethod
    def send_telemetry(cls, t):
        conf = ConfigDao().get_active()
        if env_config.TELEMETRY_ENABLE:
            t.update({"version": env_config.APP_VERSION})
            t.update({"interval": env_config.TELEMETRY_INTERVAL})
            t.update({"cluster_id": conf["cluster_id"]})
            t.update({"server_id": get_server_id()})
            t.update({"logtime": datetime.now(env_config.TZ).strftime(env_config.DATETIME_FMT)})
            try:
                env_config.API_HEADERS.update({"Content-Type": "application/json"})
                response = requests.post(
                    f"{env_config.TELEMETRY_URL}/api/usage",
                    json=t,
                    headers=env_config.API_HEADERS,
                    timeout=10,
                )
                if response.status_code not in [200, 201]:
                    logger.warn(
                        f"[{response.status_code}]:{response.text}"
                    )
            except Exception as e:
                logger.error(f"Failed to send telemetry, {e}")

    @classmethod
    def merge_transactions(cls, cache, tag):
        setattr(threading.current_thread(), "active", True)
        while getattr(threading.current_thread(), "active", False):
            with cache.lock:
                st_in = [
                    len(cache.audit_log),
                    len(cache.error_log),
                    len(cache.access_log),
                ]
                model = TransactionDao()
                for audit in cache.audit_log:
                    for log in cache.access_log:
                        if (
                            log["server_id"] == audit["server_id"]
                            and log["unique_id"] == audit["unique_id"]
                        ):
                            merged = deep_merge(log, audit)
                            merged.update({"archived": False})
                            log.update({"flushed": True})
                            cls.telemetry["net_send"] += merged["http"]["response"]["bytes"] / 1048576.0  # MB
                            cls.telemetry["net_recv"] += merged["http"]["request"]["bytes"] / 1048576.0  # MB
                            model.persist(merged)
                            break
                cache.audit_log = []
                cache.error_log = []
                t_arr = []
                for log_item in cache.access_log:
                    if "flushed" not in log_item:
                        t_arr.append(log_item)
                cls.telemetry["req_total"] += (len(cache.access_log) - len(t_arr)) / 1000.0  # K requests
                cache.access_log = t_arr
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

            time.sleep(10)
        logger.debug("merge_transactions shutdown")

    @classmethod
    def follow_file(cls, cache, file_path, log_type):
        with open(file_path, "w") as f:
            f.write("init\n")
        setattr(threading.current_thread(), "active", True)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                logger.debug(f"{file_path} for {log_type}")
                file.seek(0, 2)
                while getattr(threading.current_thread(), "active", False):
                    line = file.readline()
                    if not line:
                        time.sleep(5)
                        continue
                    t = None
                    if log_type == "ERROR":
                        t = cls.error_log(line)
                    if log_type == "ACCESS":
                        t = cls.access_log(line)
                    if log_type == "AUDIT":
                        t = cls.audit_log(line)
                    if t:
                        with cache.lock:
                            if log_type == "ERROR":
                                cache.error_log.append(t)
                            if log_type == "ACCESS":
                                cache.access_log.append(t)
                            if log_type == "AUDIT":
                                cache.audit_log.append(t)
                logger.info(f"{file_path} shutdown")

        except Exception as e:
            logger.error(f"Read file error {file_path} {e}, retry")

    @classmethod
    def resolve_status_code(cls, code):
        status_map = {503: "REJECTED", 403: "DENY"}

        if code:
            c = int(code)
            if c in status_map:
                return status_map[c]
            elif c < 400:
                return "PASSED"
            elif c >= 400:
                return "WARN"

        return "UNKNOWN"

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

                record = {
                    "server_id": server_id,
                    "unique_id": trn["unique_id"],
                    "destination": {"ip": trn["host_ip"]},
                }

                http = {}
                if "request" in trn:
                    request_raw = trn.pop("request")
                    http.update(
                        {
                            "version": request_raw["http_version"],
                        }
                    )
                    request = {
                        "method": request_raw["method"],
                        "uri": request_raw["uri"],
                        "headers": cls.parse_headers(request_raw["headers"]),
                    }
                    http.update({"request": request})

                if "response" in trn:
                    response_raw = trn.pop("response")
                    response = {
                        "status_code": response_raw["http_code"],
                        "headers": cls.parse_headers(response_raw["headers"]),
                    }
                    record.update(
                        {"action": cls.resolve_status_code(response_raw["http_code"])}
                    )
                    http.update({"response": response})
                record.update({"http": http})

                audit = {}

                if "producer" in trn:
                    producer_raw = trn.pop("producer")
                    audit.update(
                        {
                            "engine": producer_raw["modsecurity"],
                            "connector": producer_raw["connector"],
                            "mode": producer_raw["secrules_engine"],
                        }
                    )
                if "messages" in trn:
                    messages_raw = trn.pop("messages")
                    messages = []
                    for m in messages_raw:
                        msg = {
                            "text": m["message"],
                        }
                        if "details" in m:
                            d = m.pop("details")
                            msg.update(
                                {
                                    "rule_code": d["ruleId"],
                                    # "data": d["data"],
                                    "severity": d["severity"],
                                }
                            )
                            # Internal messages
                            if msg["rule_code"] in ["99"] and len(d["data"]) > 0:
                                record.update({"score": int(d["data"])})
                        if not msg["rule_code"] in ["949110", "959100", "99"]:
                            messages.append(msg)
                    audit.update({"messages": messages})
                record.update({"audit": audit})
                return record
        except Exception as e:
            logger.error(f"Error parsing log {e}")
            traceback.print_exc()

    @classmethod
    def access_log(cls, line):
        server_id = get_server_id()
        st_format = "%d/%b/%Y:%H:%M:%S %z"
        try:
            dto = json.loads(line)
            record = {
                "logtime": datetime.strptime(dto["time"], st_format).astimezone(env_config.TZ),
                "unique_id": dto["uniqueid"],
                "server_id": server_id,
                "service": {"_id": dto["service_id"]},
                "action": cls.resolve_status_code(dto["status"]),
                "limit_req_status": dto["limit_req_status"],
                "geoip_status": dto["geoip_status"],
                "rbl_status": dto["rbl_status"],
                "user_agent": cls.parse_agent(dto["user_agent"]),
                "source": {
                    "ip": dto["remote_addr"],
                    "port": dto["remote_port"],
                    "geo": SecurityFeedService.geo_info(dto["remote_addr"]),
                },
                "destination": {"ip": "", "port": dto["server_port"]},
                "http": {
                    "duration": dto["duration"],
                    "request_line": dto["request_line"],
                    "request": {
                        "method": dto["method"],
                        "bytes": dto["bytes_in"],
                    },
                    "response": {
                        "status_code": dto["status"],
                        "bytes": dto["bytes_out"],
                    },
                },
            }
            """
            if "limit_req_status" in dto and len(dto["limit_req_status"]) > 0:
                audit = {
                    "messages": [{"rule_code": "-", "text": "Request limit exceeded"}]
                }
                record.update({"audit": audit})
            """

            if dto["route_name"] != "-":
                record.update({"route_name": dto["route_name"]})
            if dto["sensor_id"] != "-":
                record.update({"sensor": {"_id": dto["sensor_id"]}})
            if dto["upstream_id"] != "-":
                record.update({"upstream": {"_id": dto["upstream_id"]}})

            if dto["upstream_id"] != "-":
                ups = {"_id": dto["upstream_id"]}
                if "target_addr" in dto and len(dto["target_addr"]) > 0:
                    ups.update({"target": dto["target_addr"]})

                record.update({"upstream": ups})
            return record
        except Exception:
            logger.error(f"Error parsing {line} {traceback.format_exc()}")
