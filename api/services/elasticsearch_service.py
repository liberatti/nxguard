import ipaddress
import json
import requests
import urllib3
from datetime import datetime
from typing import Dict, Any, List, Optional
from marshmallow import Schema, fields

from nxcore.middleware.logging_manager import logger
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema
from nxcore.common_utils import replace_tz
from api.repository.config_repository import ConfigDao
from api.model.transaction_model import TransactionSchema
from engine.elasticsearch_setup_service import ElasticsearchSetupService
import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ElasticsearchService:
    """Service for persisting and querying transactions in Elasticsearch."""

    def __init__(self, logging_conf: Optional[Dict[str, Any]] = None):
        self.logging_conf = logging_conf
        if self.logging_conf is None:
            try:
                with ConfigDao() as config_dao:
                    active = config_dao.get_active()
                    if active and isinstance(active, dict):
                        self.logging_conf = active.get("logging") or {}
            except Exception as e:
                logger.error(f"Error fetching config for Elasticsearch: {e}")
                self.logging_conf = {}

        self.setup_service = ElasticsearchSetupService(self.logging_conf)
        self.schema = TransactionSchema()
        page_class = type(
            "pagination",
            (Schema,),
            {
                "metadata": fields.Nested(PageMetaSchema, many=False),
                "data": fields.Nested(TransactionSchema, many=True),
            },
        )
        self.pageSchema = page_class()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _get_index_url(self) -> Optional[str]:
        return self.setup_service._get_index_url()

    def is_configured(self) -> bool:
        return self.setup_service.is_configured()

    def _get_auth(self) -> Optional[tuple]:
        return self.setup_service._get_auth()

    def _get_base_index_prefix(self) -> str:
        return self.setup_service._get_base_index_prefix()

    def get_search_index_pattern(self) -> str:
        """Returns the search index pattern matching all rotated daily indices (e.g. nxguard_trn*)."""
        base_prefix = self._get_base_index_prefix()
        return f"{base_prefix}*"

    def get_target_index(
        self,
        record: Optional[Dict[str, Any]] = None,
        dt: Optional[datetime] = None,
    ) -> str:
        """Computes the target daily rotated index name (e.g. nxguard_trn-2026.09.30)."""
        return self.setup_service.get_target_index(record=record, dt=dt)

    def ensure_structures(self, force: bool = False) -> bool:
        """Provisions index template, daily index, and Kibana dashboard objects via ElasticsearchSetupService."""
        return self.setup_service.ensure_structures(force=force)

    @classmethod
    def _normalize_http_headers(cls, doc: Dict[str, Any]):
        """Normalizes http.request.headers and http.response.headers into [{name, value}] array."""
        if "http" not in doc or not isinstance(doc["http"], dict):
            return
        http_copy = dict(doc["http"])
        for part in ("request", "response"):
            if part in http_copy and isinstance(http_copy[part], dict):
                part_copy = dict(http_copy[part])
                headers = part_copy.get("headers")
                if headers is not None:
                    formatted = []
                    if isinstance(headers, dict):
                        formatted = [
                            {"name": str(k), "value": str(v)}
                            for k, v in headers.items()
                        ]
                    elif isinstance(headers, list):
                        for item in headers:
                            if isinstance(item, dict):
                                val = item.get("value") if "value" in item else item.get("content", "")
                                name = item.get("name")
                                if name is not None:
                                    formatted.append({"name": str(name), "value": str(val)})
                                else:
                                    for k, v in item.items():
                                        formatted.append({"name": str(k), "value": str(v)})
                    elif isinstance(headers, str):
                        try:
                            parsed = json.loads(headers)
                            if isinstance(parsed, dict):
                                formatted = [{"name": str(k), "value": str(v)} for k, v in parsed.items()]
                        except Exception:
                            pass
                    part_copy["headers"] = formatted
                http_copy[part] = part_copy
        doc["http"] = http_copy

    @classmethod
    def _normalize_service_info(cls, doc: Dict[str, Any]):
        if "service" not in doc:
            return
        if isinstance(doc["service"], dict):
            svc = dict(doc["service"])
            svc_id = str(svc.get("_id") or svc.get("id") or svc.get("name") or "")
            if svc_id:
                svc.setdefault("_id", svc_id)
                svc.setdefault("name", svc_id)
            doc["service"] = svc
        elif doc["service"]:
            s = str(doc["service"])
            doc["service"] = {"_id": s, "name": s}

    @classmethod
    def _normalize_route(cls, doc: Dict[str, Any]):
        route_name = (
            doc.get("route_name")
            or (doc.get("route", {}).get("name") if isinstance(doc.get("route"), dict) else None)
            or ""
        )
        if route_name:
            doc["route_name"] = route_name
            if "route" not in doc or not isinstance(doc["route"], dict):
                doc["route"] = {"name": route_name}
            else:
                doc["route"].setdefault("name", route_name)

    @classmethod
    def _normalize_geo(cls, doc: Dict[str, Any]):
        if "geoip" in doc:
            if isinstance(doc["geoip"], str):
                doc["geoip"] = {"action": "", "country_code": doc["geoip"]}
            elif isinstance(doc["geoip"], dict):
                doc["geoip"] = dict(doc["geoip"])

    @classmethod
    def _normalize_reputation(cls, doc: Dict[str, Any]):
        if "reputation" in doc:
            if isinstance(doc["reputation"], dict):
                rep_obj = dict(doc["reputation"])
                if "score" in rep_obj and rep_obj["score"] is not None:
                    try:
                        rep_obj["score"] = int(rep_obj["score"])
                    except (ValueError, TypeError):
                        pass
                doc["reputation"] = rep_obj
            elif isinstance(doc["reputation"], (int, float)):
                doc["reputation"] = {"action": "", "score": int(doc["reputation"])}

    @classmethod
    def _normalize_ip_fields(cls, doc: Dict[str, Any]):
        """Ensures IP fields are valid IP addresses or None to avoid Elasticsearch mapper_parsing_exception."""
        for path in (("source", "ip"), ("source", "geo", "ip"), ("destination", "ip")):
            target = doc
            for p in path[:-1]:
                if isinstance(target, dict):
                    target = target.get(p)
                else:
                    target = None
                    break
            if isinstance(target, dict):
                leaf = path[-1]
                val = target.get(leaf)
                if val and val not in ("-", "--", "None", "null", ""):
                    try:
                        ipaddress.ip_address(str(val).strip())
                        target[leaf] = str(val).strip()
                    except (ValueError, TypeError):
                        target[leaf] = None
                else:
                    target[leaf] = None

    @classmethod
    def _format_doc(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(record)
        doc.pop("_id", None)
        if isinstance(doc.get("logtime"), datetime):
            doc["logtime"] = doc["logtime"].strftime(config.DATETIME_FMT)

        cls._normalize_http_headers(doc)
        cls._normalize_service_info(doc)
        cls._normalize_route(doc)
        cls._normalize_geo(doc)
        cls._normalize_reputation(doc)
        cls._normalize_ip_fields(doc)
        return doc

    def persist(self, record: Dict[str, Any]) -> bool:
        return self.persist_many([record])

    def persist_many(self, records: List[Dict[str, Any]]) -> bool:
        if not records:
            return True

        if not self.is_configured():
            logger.warning("Elasticsearch logging is not configured or missing URL")
            return False

        self.ensure_structures()

        url = self._get_index_url()
        if not url:
            return False
        auth = self._get_auth()

        endpoint = f"{url}/_bulk"
        headers = {"Content-Type": "application/x-ndjson"}

        bulk_lines = []
        for record in records:
            doc = self._format_doc(record)
            target_index = self.get_target_index(record=record)
            action_meta = {"index": {"_index": target_index}}
            uid = doc.get("unique_id")
            if uid and str(uid).strip() not in ("-", "null", "undefined", ""):
                action_meta["index"]["_id"] = str(uid).strip()
            bulk_lines.append(json.dumps(action_meta))
            bulk_lines.append(json.dumps(doc, default=str))

        payload = "\n".join(bulk_lines) + "\n"

        try:
            res = requests.post(
                endpoint,
                data=payload,
                headers=headers,
                auth=auth,
                timeout=5,
                verify=config.ELASTICSEARCH_SSL_VERIFY,
            )
            if res.status_code in (200, 201):
                try:
                    res_data = res.json()
                except Exception:
                    res_data = {}
                if res_data.get("errors"):
                    err_samples = []
                    for item in res_data.get("items", []):
                        for action_res in item.values():
                            if isinstance(action_res, dict) and "error" in action_res:
                                err_samples.append(
                                    f"ID {action_res.get('_id')}: {action_res.get('status')} - {action_res.get('error', {}).get('reason')}"
                                )
                                if len(err_samples) >= 3:
                                    break
                        if len(err_samples) >= 3:
                            break
                    logger.error(
                        f"Elasticsearch bulk flush had errors! Samples: {'; '.join(err_samples)}"
                    )
                    return False
                logger.debug(f"Successfully sent {len(records)} records to Elasticsearch ({endpoint})")
                return True
            logger.error(f"Elasticsearch bulk flush returned status {res.status_code}: {res.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send logs to remote Elasticsearch ({endpoint}): {e}")
            return False

    @staticmethod
    def _normalize_filters(filters) -> Dict[str, Any]:
        if not filters:
            return {}
        if isinstance(filters, dict):
            return filters
        if isinstance(filters, list):
            merged = {}
            for item in filters:
                if isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            merged.update(parsed)
                    except Exception:
                        pass
                elif isinstance(item, dict):
                    merged.update(item)
            return merged
        return {}

    _FIELD_MAP = {
        "server_id": "server_id",
        "action": "action",
        "action.keyword": "action.keyword",
        "service_id": "service._id",
        "service._id": "service._id",
        "service.id": "service._id",
        "service.name": "service.name",
        "sensor": "sensor._id",
        "sensor_id": "sensor._id",
        "sensor._id": "sensor._id",
        "sensor.id": "sensor._id",
        "sensor.name": "sensor.name",
        "upstream": "upstream._id",
        "upstream_id": "upstream._id",
        "upstream._id": "upstream._id",
        "upstream.id": "upstream._id",
        "upstream.name": "upstream.name",
        "rbl_status": "rbl_status",
        "geoip_status": "geoip_status",
        "ipxa": "ipxa",
        "route_name": "route_name",
        "route": "route_name",
        "route.name": "route_name",
        "unique_id": "unique_id",
        "score": "score",
        "limit_req_status": "limit_req_status",
        "source_ip": "source.ip",
        "source.ip": "source.ip",
        "source_port": "source.port",
        "source.port": "source.port",
        "country": "source.geo.country",
        "source.geo.country": "source.geo.country",
        "geoip.country_code": "geoip.country_code",
        "destination_host": "destination.host",
        "destination.host": "destination.host",
        "destination_ip": "destination.ip",
        "destination.ip": "destination.ip",
        "destination_port": "destination.port",
        "destination.port": "destination.port",
        "method": "http.request.method",
        "http_method": "http.request.method",
        "http.request.method": "http.request.method",
        "uri": "http.request.uri",
        "http_uri": "http.request.uri",
        "http.request.uri": "http.request.uri",
        "status": "http.response.status_code",
        "status_code": "http.response.status_code",
        "http.response.status_code": "http.response.status_code",
        "duration": "http.duration",
        "http.duration": "http.duration",
        "rate_limit": "rate_limit.action",
        "rate_limit.action": "rate_limit.action",
        "user_agent": "user_agent.family",
        "user_agent.family": "user_agent.family",
        "mtls_verified": "mtls.verified",
        "mtls.verified": "mtls.verified",
    }

    @classmethod
    def _build_query_dsl(cls, dt_start=None, dt_end=None, filters=None) -> Dict[str, Any]:
        must_clauses: List[Dict[str, Any]] = []

        time_range: Dict[str, str] = {}
        if dt_start:
            time_range["gte"] = dt_start.strftime(config.DATETIME_FMT) if hasattr(dt_start, "strftime") else str(dt_start)
        if dt_end:
            time_range["lte"] = dt_end.strftime(config.DATETIME_FMT) if hasattr(dt_end, "strftime") else str(dt_end)
        if time_range:
            must_clauses.append({"range": {"logtime": time_range}})

        filter_dict = cls._normalize_filters(filters)
        for key, val in filter_dict.items():
            if key in ["rule_code", "audit.rule_code", "audit.messages.rule_code"]:
                rule_val = str(val)
                must_clauses.append(
                    {
                        "bool": {
                            "should": [
                                {"term": {"audit.messages.rule_code": rule_val}},
                                {"term": {"audit.messages.ruleId": rule_val}},
                            ]
                        }
                    }
                )
                continue

            if key.startswith("header.") or key.startswith("http.request.headers."):
                h_name = key.split(".")[-1]
                must_clauses.append(
                    {
                        "nested": {
                            "path": "http.request.headers",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"term": {"http.request.headers.name": h_name}},
                                        {"term": {"http.request.headers.value": str(val)}},
                                    ]
                                }
                            },
                        }
                    }
                )
                continue

            field = cls._FIELD_MAP.get(key, key)
            if isinstance(val, list):
                must_clauses.append({"terms": {field: val}})
            elif isinstance(val, dict):
                for op, op_val in val.items():
                    if op in ["$gte", "$lte", "$gt", "$lt"]:
                        must_clauses.append({"range": {field: {op[1:]: op_val}}})
                    elif op == "$ne":
                        must_clauses.append({"bool": {"must_not": [{"term": {field: op_val}}]}})
                    elif op in ["$like", "$contains"]:
                        pattern = f"*{op_val}*" if not str(op_val).startswith("*") else str(op_val)
                        must_clauses.append({"wildcard": {field: pattern}})
                    elif op == "$in" and isinstance(op_val, list):
                        must_clauses.append({"terms": {field: op_val}})
            elif key in ["uri", "http_uri", "http.request.uri"]:
                pattern = f"*{val}*" if not str(val).startswith("*") else str(val)
                must_clauses.append({"wildcard": {field: pattern}})
            else:
                must_clauses.append({"term": {field: val}})

        return {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

    def get_by_id(self, trn_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a transaction record by unique_id or internal document ID."""
        if not self.is_configured() or not trn_id:
            return None

        url = self._get_index_url()
        if not url:
            return None
        search_index = self.get_search_index_pattern()

        search_query = {
            "size": 1,
            "query": {
                "bool": {
                    "should": [
                        {"term": {"unique_id": trn_id}},
                        {"term": {"_id": trn_id}},
                    ]
                }
            },
        }

        try:
            res = requests.post(
                f"{url}/{search_index}/_search",
                json=search_query,
                headers={"Content-Type": "application/json"},
                auth=self._get_auth(),
                timeout=5,
                verify=config.ELASTICSEARCH_SSL_VERIFY,
            )
            if res.status_code == 200:
                hits = res.json().get("hits", {}).get("hits", [])
                if hits:
                    source = hits[0].get("_source", {})
                    source["_id"] = hits[0].get("_id")
                    return source
        except Exception as e:
            logger.error(f"Error querying Elasticsearch for transaction {trn_id}: {e}")

        return None

    def get_all(
        self,
        pagination: Optional[Dict[str, Any]] = None,
        dt_start=None,
        dt_end=None,
        filters=None,
    ) -> Dict[str, Any]:
        """Queries transactions with filters, pagination, and logtime sorting."""
        if not self.is_configured():
            return {"metadata": pagination or {"total_elements": 0, "page": 1, "per_page": 10}, "data": []}

        url = self._get_index_url()
        if not url:
            return {"metadata": pagination or {"total_elements": 0, "page": 1, "per_page": 10}, "data": []}

        search_index = self.get_search_index_pattern()
        page = pagination.get("page", 1) if pagination else 1
        per_page = pagination.get("per_page", 10) if pagination else 10
        from_idx = (page - 1) * per_page

        search_payload = {
            "from": from_idx,
            "size": per_page,
            "sort": [{"logtime": {"order": "desc"}}],
            "query": self._build_query_dsl(dt_start=dt_start, dt_end=dt_end, filters=filters),
        }

        try:
            res = requests.post(
                f"{url}/{search_index}/_search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
                auth=self._get_auth(),
                timeout=10,
                verify=config.ELASTICSEARCH_SSL_VERIFY,
            )
            if res.status_code == 200:
                data_json = res.json()
                total_val = data_json.get("hits", {}).get("total", {})
                total = total_val.get("value", 0) if isinstance(total_val, dict) else (total_val or 0)
                raw_hits = data_json.get("hits", {}).get("hits", [])
                rows = []
                for hit in raw_hits:
                    src = hit.get("_source", {})
                    src["_id"] = hit.get("_id")
                    rows.append(src)

                meta = dict(pagination) if pagination else {"total_elements": total, "page": 1, "per_page": total}
                meta["total_elements"] = total
                return {"metadata": meta, "data": rows}
            logger.error(f"Elasticsearch search returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error executing Elasticsearch get_all query: {e}")

        meta = pagination or {"total_elements": 0, "page": 1, "per_page": 10}
        meta["total_elements"] = 0
        return {"metadata": meta, "data": []}

    def get_tpm(self, st_date, ed_date, filters=None) -> List[Dict[str, Any]]:
        """Calculates Transactions Per Minute (TPM) using Elasticsearch date histogram aggregations."""
        if not self.is_configured():
            return []

        url = self._get_index_url()
        if not url:
            return []
        search_index = self.get_search_index_pattern()

        search_payload = {
            "size": 0,
            "query": self._build_query_dsl(dt_start=st_date, dt_end=ed_date, filters=filters),
            "aggs": {
                "by_minute": {
                    "date_histogram": {
                        "field": "logtime",
                        "fixed_interval": "1m",
                        "min_doc_count": 1,
                    },
                    "aggs": {
                        "by_action": {
                            "terms": {
                                "field": "action.keyword",
                                "missing": "ALLOWED",
                            }
                        },
                        "bytes_in": {"sum": {"field": "http.request.bytes"}},
                        "bytes_out": {"sum": {"field": "http.response.bytes"}},
                    },
                }
            },
        }

        try:
            res = requests.post(
                f"{url}/{search_index}/_search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
                auth=self._get_auth(),
                timeout=10,
                verify=config.ELASTICSEARCH_SSL_VERIFY,
            )
            if res.status_code == 200:
                buckets = res.json().get("aggregations", {}).get("by_minute", {}).get("buckets", [])
                tpm_list = []

                for b in buckets:
                    key_str = b.get("key_as_string")
                    key_millis = b.get("key")
                    dt = None
                    if key_str:
                        try:
                            dt = datetime.fromisoformat(key_str.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    if not dt and key_millis:
                        try:
                            dt = datetime.fromtimestamp(key_millis / 1000.0, tz=config.TZ)
                        except Exception:
                            pass

                    if not dt:
                        continue

                    dt = replace_tz(dt)
                    actions = {
                        str(ab.get("key") or "ALLOWED").upper(): ab.get("doc_count", 0)
                        for ab in b.get("by_action", {}).get("buckets", [])
                    }

                    tpm_list.append(
                        {
                            "_id": {
                                "year": dt.year,
                                "month": dt.month,
                                "day": dt.day,
                                "hour": dt.hour,
                                "minute": dt.minute,
                            },
                            "count": b.get("doc_count", 0),
                            "bytes_in": int(b.get("bytes_in", {}).get("value", 0)),
                            "bytes_out": int(b.get("bytes_out", {}).get("value", 0)),
                            "actions": actions,
                        }
                    )
                return tpm_list
            logger.error(f"Elasticsearch TPM aggregation returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Error querying Elasticsearch TPM stats: {e}")

        return []
