import json
import requests
import urllib3
from datetime import datetime
from typing import Dict, Any, List, Optional
from marshmallow import Schema, fields

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from nxcore.middleware.logging_manager import logger
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema
from nxcore.common_utils import replace_tz
from api.repository.config_repository import ConfigDao
from api.model.transaction_model import TransactionSchema
import config
from api.services.transaction_schema_opensearch import (
    INDEX_TEMPLATE_NAME,
    DEFAULT_SETTINGS,
    DEFAULT_MAPPINGS,
    build_index_template_payload,
    build_index_pattern_fields,
    build_index_pattern_attributes,
    build_action_timeline_vis,
    build_action_pie_vis,
    build_status_timeline_vis,
    build_top_services_vis,
    build_visitors_by_user_agent_vis,
    build_host_visits_bytes_table_vis,
    build_visitors_map_vis,
    get_default_visualizations,
    get_default_dashboard,
)


class OpenSearchService:
    """Service for provisioning structures, persisting transactions, and querying OpenSearch / Elasticsearch."""

    _structures_initialized: bool = False

    DEFAULT_SETTINGS = DEFAULT_SETTINGS
    DEFAULT_MAPPINGS = DEFAULT_MAPPINGS

    def __init__(self, logging_conf: Optional[Dict[str, Any]] = None):
        self.logging_conf = logging_conf
        if self.logging_conf is None:
            try:
                with ConfigDao() as config_dao:
                    active = config_dao.get_active()
                    if active and isinstance(active, dict):
                        self.logging_conf = active.get("logging") or {}
            except Exception as e:
                logger.error(f"Error fetching config for OpenSearch: {e}")
                self.logging_conf = {}

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

    def is_configured(self) -> bool:
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return False
        return bool(self.logging_conf.get("url"))

    def _get_auth(self) -> Optional[tuple]:
        username = self.logging_conf.get("username")
        password = self.logging_conf.get("password")
        return (username, password) if username and password else None

    def _get_base_index_prefix(self) -> str:
        configured = (self.logging_conf.get("index") or "nxguard_trn").strip()
        prefix = configured.split("%")[0].rstrip("*").rstrip("-").rstrip(".")
        return prefix or "nxguard_trn"

    def get_search_index_pattern(self) -> str:
        """Returns the search index pattern matching all rotated daily indices (e.g. nxguard_trn*)."""
        base_prefix = self._get_base_index_prefix()
        return f"{base_prefix}*"

    def get_target_index(
        self,
        record: Optional[Dict[str, Any]] = None,
        dt: Optional[datetime] = None,
    ) -> str:
        """Computes the target daily rotated index name (e.g. nxguard_trn-2026.09.09)."""
        target_dt = dt
        if not target_dt and record:
            logtime_val = record.get("logtime")
            if isinstance(logtime_val, datetime):
                target_dt = logtime_val
            elif isinstance(logtime_val, str):
                if "T" in logtime_val or (len(logtime_val) >= 10 and logtime_val[4] == "-" and logtime_val[7] == "-"):
                    try:
                        target_dt = datetime.fromisoformat(
                            logtime_val.replace("Z", "+00:00")
                        )
                    except Exception:
                        pass
                if not target_dt:
                    for fmt in config.COMMON_LOG_FORMATS:
                        try:
                            target_dt = datetime.strptime(logtime_val, fmt)
                            break
                        except (ValueError, TypeError):
                            continue

        if not target_dt:
            target_dt = datetime.now(config.TZ)

        configured = (self.logging_conf.get("index") or "nxguard_trn").strip()
        if "%" in configured:
            try:
                return target_dt.strftime(configured)
            except Exception:
                pass

        base_prefix = self._get_base_index_prefix()
        date_suffix = target_dt.strftime("%Y.%m.%d")
        return f"{base_prefix}-{date_suffix}"

    def _get_dashboard_url(self) -> Optional[str]:
        dash_url = self.logging_conf.get("dashboard_url")
        if not dash_url and self.logging_conf.get("url"):
            u = self.logging_conf.get("url", "")
            if ":9200" in u:
                dash_url = u.replace(":9200", ":5601")
        return dash_url.rstrip("/") if dash_url else None

    def _post_saved_object(
        self,
        obj_type: str,
        obj_id: str,
        attributes: Dict[str, Any],
        references: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        dash_url = self._get_dashboard_url()
        if not dash_url:
            logger.warning(
                f"OpenSearch Dashboards URL could not be resolved for {obj_type} '{obj_id}'"
            )
            return False

        auth = self._get_auth()
        headers = {
            "Content-Type": "application/json",
            "osd-xsrf": "true",
            "kbn-xsrf": "true",
        }
        payload: Dict[str, Any] = {"attributes": attributes}
        if references:
            payload["references"] = references

        endpoint = f"{dash_url}/api/saved_objects/{obj_type}/{obj_id}?overwrite=true"
        try:
            res = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201, 409):
                logger.info(
                    f"OpenSearch Dashboards {obj_type} '{obj_id}' created/updated successfully at {dash_url}"
                )
                return True
            else:
                logger.warning(
                    f"OpenSearch Dashboards returned status {res.status_code} for {obj_type} '{obj_id}': {res.text}"
                )
        except Exception as e:
            logger.warning(f"Failed to create {obj_type} '{obj_id}' at {endpoint}: {e}")
        return False

    def ensure_structures(self, force: bool = False) -> bool:
        """Provisions index template, daily index, index pattern, visualizations, and dashboard."""
        if not self.is_configured():
            logger.warning("OpenSearch logging is not configured; skipping structure provisioning.")
            return False

        if not force and OpenSearchService._structures_initialized:
            return True

        logger.info("Initializing OpenSearch templates, indices, and Dashboards objects...")
        tmpl_ok = self.create_index_template()
        today_idx = self.get_target_index()
        idx_ok = self.create_index_if_not_exists(today_idx)
        pat_ok = self.create_index_pattern()
        vis_ok = self.create_visualizations()
        dash_ok = self.create_dashboard()

        OpenSearchService._structures_initialized = True
        logger.info(
            f"OpenSearch structure initialization complete: template={tmpl_ok}, index={idx_ok}, index_pattern={pat_ok}, visualizations={vis_ok}, dashboard={dash_ok}"
        )
        return tmpl_ok and idx_ok

    def create_index_template(self, template_name: str = INDEX_TEMPLATE_NAME) -> bool:
        """Creates composable or legacy index template in OpenSearch / Elasticsearch."""
        if not self.is_configured():
            return False

        url = self.logging_conf.get("url", "").rstrip("/")
        base_prefix = self._get_base_index_prefix()
        auth = self._get_auth()
        headers = {"Content-Type": "application/json"}

        # Try composable index template API (OpenSearch 1+, Elasticsearch 7.8+)
        composable_payload = build_index_template_payload(base_prefix, composable=True)
        try:
            res = requests.put(
                f"{url}/_index_template/{template_name}",
                json=composable_payload,
                headers=headers,
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.info(
                    f"OpenSearch index template '{template_name}' created successfully"
                )
                return True
        except Exception as e:
            logger.debug(f"Failed to create composable template {template_name}: {e}")

        # Fallback to legacy index template API (_template/name)
        legacy_payload = build_index_template_payload(base_prefix, composable=False)
        try:
            res = requests.put(
                f"{url}/_template/{template_name}",
                json=legacy_payload,
                headers=headers,
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.info(
                    f"OpenSearch legacy index template '{template_name}' created successfully"
                )
                return True
            else:
                logger.warning(
                    f"Failed to create index template on OpenSearch: {res.status_code} {res.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error creating index template on OpenSearch: {e}")
            return False

    def _build_index_pattern_fields(self) -> str:
        """Generates the field schema definition required by OpenSearch Dashboards index patterns."""
        return build_index_pattern_fields()

    def create_index_pattern(self, pattern_title: Optional[str] = None) -> bool:
        """Creates an index-pattern saved object in OpenSearch Dashboards."""
        if not self.is_configured():
            return False

        base_prefix = self._get_base_index_prefix()
        title = pattern_title or f"{base_prefix}*"
        pattern_id = base_prefix
        attributes = build_index_pattern_attributes(title)
        return self._post_saved_object("index-pattern", pattern_id, attributes)

    def _build_action_timeline_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_action_timeline_vis(pattern_id)

    def _build_action_pie_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_action_pie_vis(pattern_id)

    def _build_status_timeline_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_status_timeline_vis(pattern_id)

    def _build_top_services_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_top_services_vis(pattern_id)

    def _build_visitors_by_user_agent_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_visitors_by_user_agent_vis(pattern_id)

    def _build_host_visits_bytes_table_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_host_visits_bytes_table_vis(pattern_id)

    def _build_visitors_map_vis(self, pattern_id: str) -> Dict[str, Any]:
        return build_visitors_map_vis(pattern_id)

    def create_visualizations(self) -> bool:
        """Creates the default set of visualizations in OpenSearch Dashboards."""
        if not self.is_configured():
            return False

        base_prefix = self._get_base_index_prefix()
        vis_items = get_default_visualizations(base_prefix)

        created_count = 0
        for vis_id, vis_attrs, ref in vis_items:
            res = self._post_saved_object(
                "visualization", vis_id, vis_attrs, references=ref
            )
            if res:
                created_count += 1
        logger.info(
            f"OpenSearch Dashboards {created_count}/{len(vis_items)} visualizations initialized successfully"
        )
        return created_count == len(vis_items)

    def create_dashboard(self, dashboard_title: Optional[str] = None) -> bool:
        """Creates the NxGuard overview dashboard in OpenSearch Dashboards."""
        if not self.is_configured():
            return False

        base_prefix = self._get_base_index_prefix()
        dash_id, attributes, references = get_default_dashboard(
            base_prefix, title=dashboard_title
        )

        return self._post_saved_object(
            "dashboard", dash_id, attributes, references=references
        )

    def create_index_if_not_exists(self, index_name: Optional[str] = None) -> bool:
        """Checks if index exists; creates it with settings and mappings if missing."""
        if not self.is_configured():
            return False

        url = self.logging_conf.get("url", "").rstrip("/")
        idx = index_name or self.get_target_index()
        auth = self._get_auth()
        headers = {"Content-Type": "application/json"}

        try:
            check_res = requests.head(
                f"{url}/{idx}",
                auth=auth,
                timeout=5,
                verify=False,
            )
            if check_res.status_code == 200:
                logger.info(f"OpenSearch index '{idx}' is ready (already exists)")
                return True
        except Exception as e:
            logger.debug(f"Index existence check failed for {idx}: {e}")

        payload = {
            "settings": self.DEFAULT_SETTINGS,
            "mappings": self.DEFAULT_MAPPINGS,
        }

        try:
            res = requests.put(
                f"{url}/{idx}",
                json=payload,
                headers=headers,
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.info(f"OpenSearch index '{idx}' created successfully")
                return True
            elif (
                res.status_code == 400
                and "resource_already_exists_exception" in res.text
            ):
                logger.info(f"OpenSearch index '{idx}' is ready (already exists)")
                return True
            else:
                logger.warning(
                    f"OpenSearch index creation returned status {res.status_code}: {res.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error creating OpenSearch index {idx}: {e}")
            return False

    @staticmethod
    def _headers_to_list(headers: Any) -> List[Dict[str, str]]:
        if isinstance(headers, dict):
            return [{"name": str(k), "value": str(v)} for k, v in headers.items()]
        elif isinstance(headers, list):
            formatted = []
            for item in headers:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    formatted.append(
                        {"name": str(item["name"]), "value": str(item["value"])}
                    )
                elif isinstance(item, dict):
                    for k, v in item.items():
                        formatted.append({"name": str(k), "value": str(v)})
            return formatted
        elif isinstance(headers, str):
            try:
                parsed = json.loads(headers)
                if isinstance(parsed, dict):
                    return [
                        {"name": str(k), "value": str(v)} for k, v in parsed.items()
                    ]
            except Exception:
                pass
        return []

    @classmethod
    def _format_doc(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(record)
        doc.pop("_id", None)
        if isinstance(doc.get("logtime"), datetime):
            doc["logtime"] = doc["logtime"].strftime(config.DATETIME_FMT)

        if "http" in doc and isinstance(doc["http"], dict):
            http_copy = dict(doc["http"])
            if "request" in http_copy and isinstance(http_copy["request"], dict):
                req_copy = dict(http_copy["request"])
                if "headers" in req_copy:
                    req_copy["headers"] = cls._headers_to_list(req_copy["headers"])
                http_copy["request"] = req_copy

            if "response" in http_copy and isinstance(http_copy["response"], dict):
                res_copy = dict(http_copy["response"])
                if "headers" in res_copy:
                    res_copy["headers"] = cls._headers_to_list(res_copy["headers"])
                http_copy["response"] = res_copy

            doc["http"] = http_copy

        # Normalize service
        if "service" in doc:
            if isinstance(doc["service"], dict):
                svc = dict(doc["service"])
                svc_id = str(svc.get("_id") or svc.get("id") or svc.get("name") or "")
                if svc_id:
                    if "_id" not in svc or not svc["_id"]:
                        svc["_id"] = svc_id
                    if "name" not in svc or not svc["name"]:
                        svc["name"] = svc_id
                doc["service"] = svc
            elif doc["service"]:
                s = str(doc["service"])
                doc["service"] = {"_id": s, "name": s}

        # Normalize route / route_name
        route_name = (
            doc.get("route_name")
            or (
                doc.get("route", {}).get("name")
                if isinstance(doc.get("route"), dict)
                else None
            )
            or ""
        )
        if route_name:
            doc["route_name"] = route_name
            if "route" not in doc or not isinstance(doc["route"], dict):
                doc["route"] = {"name": route_name}
            elif isinstance(doc["route"], dict) and "name" not in doc["route"]:
                doc["route"]["name"] = route_name

        # Normalize geo / geoip
        if "geoip" in doc:
            if isinstance(doc["geoip"], dict):
                doc["geoip"] = dict(doc["geoip"])
            elif isinstance(doc["geoip"], str):
                doc["geoip"] = {"action": "", "country_code": doc["geoip"]}

        # Normalize reputation
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

        return doc

    def persist(self, record: Dict[str, Any]) -> bool:
        return self.persist_many([record])

    def persist_many(self, records: List[Dict[str, Any]]) -> bool:
        if not records:
            return True

        if not self.is_configured():
            logger.warning("OpenSearch logging is not configured or missing URL")
            return False

        self.ensure_structures()

        url = self.logging_conf.get("url", "").rstrip("/")
        auth = self._get_auth()

        endpoint = f"{url}/_bulk"
        headers = {"Content-Type": "application/x-ndjson"}

        bulk_lines = []
        for record in records:
            doc = self._format_doc(record)
            target_index = self.get_target_index(record=record)
            action_meta = {"index": {"_index": target_index}}
            if doc.get("unique_id"):
                action_meta["index"]["_id"] = doc["unique_id"]
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
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.debug(
                    f"Successfully sent {len(records)} records to OpenSearch ({endpoint})"
                )
                return True
            else:
                logger.error(
                    f"OpenSearch bulk flush returned status {res.status_code}: {res.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to send logs to remote OpenSearch ({endpoint}): {e}")
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
    def _build_query_dsl(
        cls, dt_start=None, dt_end=None, filters=None
    ) -> Dict[str, Any]:
        must_clauses: List[Dict[str, Any]] = []

        # Time range clause
        time_range: Dict[str, str] = {}
        if dt_start:
            time_range["gte"] = (
                dt_start.strftime(config.DATETIME_FMT)
                if hasattr(dt_start, "strftime")
                else str(dt_start)
            )
        if dt_end:
            time_range["lte"] = (
                dt_end.strftime(config.DATETIME_FMT)
                if hasattr(dt_end, "strftime")
                else str(dt_end)
            )
        if time_range:
            must_clauses.append({"range": {"logtime": time_range}})

        filter_dict = cls._normalize_filters(filters)
        for key, val in filter_dict.items():
            if key in ["rule_code", "audit.rule_code", "audit.messages.rule_code"]:
                rule_val = str(val)
                must_clauses.append(
                    {
                        "nested": {
                            "path": "audit.messages",
                            "query": {
                                "bool": {
                                    "should": [
                                        {
                                            "term": {
                                                "audit.messages.rule_code": rule_val
                                            }
                                        },
                                        {"term": {"audit.messages.ruleId": rule_val}},
                                    ]
                                }
                            },
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
                                        {
                                            "term": {
                                                "http.request.headers.value": str(val)
                                            }
                                        },
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
                        must_clauses.append(
                            {"bool": {"must_not": [{"term": {field: op_val}}]}}
                        )
                    elif op in ["$like", "$contains"]:
                        pattern = (
                            f"*{op_val}*"
                            if not str(op_val).startswith("*")
                            else str(op_val)
                        )
                        must_clauses.append({"wildcard": {field: pattern}})
                    elif op == "$in" and isinstance(op_val, list):
                        must_clauses.append({"terms": {field: op_val}})
            elif key in ["uri", "http_uri", "http.request.uri"]:
                pattern = f"*{val}*" if not str(val).startswith("*") else str(val)
                must_clauses.append({"wildcard": {field: pattern}})
            else:
                must_clauses.append({"term": {field: val}})

        if not must_clauses:
            return {"match_all": {}}
        return {"bool": {"must": must_clauses}}

    def get_by_id(self, trn_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a transaction record by unique_id or internal document ID."""
        if not self.is_configured() or not trn_id:
            return None

        url = self.logging_conf.get("url", "").rstrip("/")
        search_index = self.get_search_index_pattern()
        auth = self._get_auth()
        headers = {"Content-Type": "application/json"}

        # Search by unique_id term across all rotated indices
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
                headers=headers,
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code == 200:
                hits = res.json().get("hits", {}).get("hits", [])
                if hits:
                    source = hits[0].get("_source", {})
                    source["_id"] = hits[0].get("_id")
                    return source
        except Exception as e:
            logger.error(f"Error querying OpenSearch for transaction {trn_id}: {e}")

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
            return {
                "metadata": pagination
                or {"total_elements": 0, "page": 1, "per_page": 10},
                "data": [],
            }

        url = self.logging_conf.get("url", "").rstrip("/")
        search_index = self.get_search_index_pattern()
        auth = self._get_auth()
        headers = {"Content-Type": "application/json"}

        page = pagination.get("page", 1) if pagination else 1
        per_page = pagination.get("per_page", 10) if pagination else 10
        from_idx = (page - 1) * per_page

        query_dsl = self._build_query_dsl(
            dt_start=dt_start, dt_end=dt_end, filters=filters
        )

        search_payload = {
            "from": from_idx,
            "size": per_page,
            "sort": [{"logtime": {"order": "desc"}}],
            "query": query_dsl,
        }

        try:
            res = requests.post(
                f"{url}/{search_index}/_search",
                json=search_payload,
                headers=headers,
                auth=auth,
                timeout=10,
                verify=False,
            )
            if res.status_code == 200:
                data_json = res.json()
                total_val = data_json.get("hits", {}).get("total", {})
                total = (
                    total_val.get("value", 0)
                    if isinstance(total_val, dict)
                    else (total_val or 0)
                )
                raw_hits = data_json.get("hits", {}).get("hits", [])
                rows = []
                for hit in raw_hits:
                    src = hit.get("_source", {})
                    src["_id"] = hit.get("_id")
                    rows.append(src)

                if pagination:
                    pagination["total_elements"] = total
                else:
                    pagination = {"total_elements": total, "page": 1, "per_page": total}

                return {"metadata": pagination, "data": rows}
            else:
                logger.error(
                    f"OpenSearch search returned status {res.status_code}: {res.text}"
                )
        except Exception as e:
            logger.error(f"Error executing OpenSearch get_all query: {e}")

        meta = pagination or {"total_elements": 0, "page": 1, "per_page": 10}
        meta["total_elements"] = 0
        return {"metadata": meta, "data": []}

    def get_tpm(self, st_date, ed_date, filters=None) -> List[Dict[str, Any]]:
        """Calculates Transactions Per Minute (TPM) using OpenSearch date histogram aggregations."""
        if not self.is_configured():
            return []

        url = self.logging_conf.get("url", "").rstrip("/")
        search_index = self.get_search_index_pattern()
        auth = self._get_auth()
        headers = {"Content-Type": "application/json"}

        query_dsl = self._build_query_dsl(
            dt_start=st_date, dt_end=ed_date, filters=filters
        )

        search_payload = {
            "size": 0,
            "query": query_dsl,
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
                                "field": "action",
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
                headers=headers,
                auth=auth,
                timeout=10,
                verify=False,
            )
            if res.status_code == 200:
                aggs = res.json().get("aggregations", {})
                buckets = aggs.get("by_minute", {}).get("buckets", [])
                tpm_list = []

                for b in buckets:
                    key_str = b.get("key_as_string")
                    key_millis = b.get("key")
                    dt = None
                    if key_str:
                        try:
                            clean_str = key_str.replace("Z", "+00:00")
                            dt = datetime.fromisoformat(clean_str)
                        except Exception:
                            pass
                    if not dt and key_millis:
                        try:
                            dt = datetime.fromtimestamp(
                                key_millis / 1000.0, tz=config.TZ
                            )
                        except Exception:
                            pass

                    if not dt:
                        continue

                    dt = replace_tz(dt)

                    actions = {}
                    for ab in b.get("by_action", {}).get("buckets", []):
                        act_key = str(ab.get("key") or "ALLOWED").upper()
                        actions[act_key] = ab.get("doc_count", 0)

                    bytes_in = int(b.get("bytes_in", {}).get("value", 0))
                    bytes_out = int(b.get("bytes_out", {}).get("value", 0))

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
                            "bytes_in": bytes_in,
                            "bytes_out": bytes_out,
                            "actions": actions,
                        }
                    )

                return tpm_list
            else:
                logger.error(
                    f"OpenSearch TPM aggregation returned status {res.status_code}: {res.text}"
                )
        except Exception as e:
            logger.error(f"Error querying OpenSearch TPM stats: {e}")

        return []
