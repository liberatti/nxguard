import json
import os
import requests
import urllib3
from datetime import datetime
from typing import Dict, Any, Optional

from nxcore.middleware.logging_manager import logger
from api.repository.config_repository import ConfigDao
import config
from config import INDEX_TEMPLATE_NAME, ELASTICSEARCH_SEED_DIR

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ElasticsearchSetupService:
    """Service responsible for provisioning Elasticsearch templates, indices, user credentials, and Kibana dashboards."""

    _structures_initialized: bool = False

    @staticmethod
    def load_seed_json(relative_path: str) -> Optional[Dict[str, Any]]:
        """Loads a JSON seed file directly from ELASTICSEARCH_SEED_DIR."""
        path = os.path.join(ELASTICSEARCH_SEED_DIR, relative_path)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load seed JSON from {path}: {e}")
                return None
        logger.warning(f"Seed JSON file not found at {path}")
        return None

    def __init__(self, logging_conf: Optional[Dict[str, Any]] = None):
        self.logging_conf = logging_conf
        if self.logging_conf is None:
            try:
                with ConfigDao() as config_dao:
                    active = config_dao.get_active()
                    if active and isinstance(active, dict):
                        self.logging_conf = active.get("logging") or {}
            except Exception as e:
                logger.error(f"Error fetching config for Elasticsearch setup: {e}")
                self.logging_conf = {}

        self.DEFAULT_SETTINGS: Dict[str, Any] = self.load_seed_json(
            "index_settings.json"
        ) or {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "5s",
            }
        }
        self.DEFAULT_MAPPINGS: Dict[str, Any] = (
            self.load_seed_json("index_mappings.json") or {}
        )

    def _get_index_url(self) -> Optional[str]:
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return None
        url = (
            self.logging_conf.get("index_url") or self.logging_conf.get("url") or ""
        ).strip()
        return url.rstrip("/") if url else None

    def is_configured(self) -> bool:
        return bool(self._get_index_url())

    def _get_auth(self) -> Optional[tuple]:
        """Returns (username, password) tuple for Elasticsearch Basic Auth."""
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return None
        username = self.logging_conf.get("index_username") or self.logging_conf.get(
            "username"
        )
        password = (
            self.logging_conf.get("index_password")
            or self.logging_conf.get("password")
            or ""
        )
        if username:
            return (str(username).strip(), str(password))
        return None

    def _get_dashboard_url(self) -> Optional[str]:
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return None
        dash_url = (self.logging_conf.get("dashboard_url") or "").strip()
        return dash_url.rstrip("/") if dash_url else None

    def _get_dashboard_auth(self) -> Optional[tuple]:
        """Returns (username, password) tuple for Kibana REST API calls."""
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return None
        username = self.logging_conf.get("dashboard_username")
        password = self.logging_conf.get("dashboard_password") or ""
        if username and str(username).strip().lower() != "kibana_system":
            return (str(username).strip(), str(password))
        return self._get_auth()

    def _get_base_index_prefix(self) -> str:
        if not self.logging_conf or not isinstance(self.logging_conf, dict):
            return "nxguard_trn"
        configured = (self.logging_conf.get("index") or "nxguard_trn").strip()
        return (
            configured.split("%")[0].rstrip("*").rstrip("-").rstrip(".")
            or "nxguard_trn"
        )

    def get_target_index(
        self,
        record: Optional[Dict[str, Any]] = None,
        dt: Optional[datetime] = None,
    ) -> str:
        """Computes the target daily rotated index name (e.g. nxguard_trn-2026.09.30)."""
        target_dt = dt
        if not target_dt and record and record.get("logtime"):
            logtime_val = record["logtime"]
            if isinstance(logtime_val, datetime):
                target_dt = logtime_val
            elif isinstance(logtime_val, str):
                try:
                    target_dt = datetime.fromisoformat(
                        logtime_val.replace("Z", "+00:00")
                    )
                except Exception:
                    pass

        if not target_dt:
            target_dt = datetime.now(config.TZ)

        base_prefix = self._get_base_index_prefix()
        date_suffix = target_dt.strftime("%Y.%m.%d")
        return f"{base_prefix}-{date_suffix}"

    def setup_dashboard_user(self) -> bool:
        """Sets the dashboard_password for dashboard_username on Elasticsearch."""
        if not self.is_configured():
            return False

        dash_user = self.logging_conf.get("dashboard_username")
        dash_pass = self.logging_conf.get("dashboard_password")
        if not dash_user or dash_pass is None:
            return True

        index_url = self._get_index_url()
        endpoint = f"{index_url}/_security/user/{str(dash_user).strip()}/_password"
        try:
            res = requests.post(
                endpoint,
                json={"password": str(dash_pass)},
                headers={"Content-Type": "application/json"},
                auth=self._get_auth(),
                timeout=5,
                verify=False,
            )
            if res.status_code == 200:
                logger.info(
                    f"Elasticsearch user '{dash_user}' password updated successfully."
                )
                return True
            logger.warning(
                f"Failed to update Elasticsearch password for '{dash_user}': {res.status_code} {res.text}"
            )
            return False
        except Exception as e:
            logger.warning(
                f"Error setting Elasticsearch password for '{dash_user}': {e}"
            )
            return False

    def create_index_template(self, template_name: str = INDEX_TEMPLATE_NAME) -> bool:
        """Creates composable index template in Elasticsearch."""
        if not self.is_configured():
            return False

        url = self._get_index_url()
        payload = self.load_seed_json("index_template.json")
        if not payload:
            return False

        base_prefix = self._get_base_index_prefix()
        payload["index_patterns"] = [f"{base_prefix}*", f"{base_prefix}-*"]

        try:
            res = requests.put(
                f"{url}/_index_template/{template_name}",
                json=payload,
                headers={"Content-Type": "application/json"},
                auth=self._get_auth(),
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.info(
                    f"Elasticsearch index template '{template_name}' created successfully"
                )
                return True
            logger.warning(
                f"Failed to create index template: {res.status_code} {res.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Error creating index template: {e}")
            return False

    def create_index_if_not_exists(self, index_name: Optional[str] = None) -> bool:
        """Checks if index exists; creates it with seed settings and mappings if missing."""
        if not self.is_configured():
            return False

        url = self._get_index_url()
        idx = index_name or self.get_target_index()
        auth = self._get_auth()

        try:
            check_res = requests.get(
                f"{url}/{idx}/_mapping", auth=auth, timeout=5, verify=False
            )
            if check_res.status_code == 200:
                mapping_data = check_res.json().get(idx, {}).get("mappings", {})
                props = mapping_data.get("properties", {})
                is_invalid = (
                    props.get("action", {}).get("type") == "text"
                    or props.get("service", {}).get("properties", {}).get("name", {}).get("type") == "text"
                    or props.get("route_name", {}).get("type") == "text"
                    or props.get("destination", {}).get("properties", {}).get("host", {}).get("type") == "text"
                    or props.get("source", {}).get("properties", {}).get("geo", {}).get("properties", {}).get("country", {}).get("type") == "text"
                    or props.get("user_agent", {}).get("properties", {}).get("family", {}).get("type") == "text"
                    or props.get("http", {}).get("properties", {}).get("request", {}).get("properties", {}).get("uri", {}).get("type") == "text"
                    or props.get("http", {}).get("properties", {}).get("referer", {}).get("type") == "text"
                )
                if is_invalid:
                    logger.warning(
                        f"Elasticsearch index '{idx}' has incompatible dynamic text mappings. Recreating with seed template mappings..."
                    )
                    requests.delete(f"{url}/{idx}", auth=auth, timeout=5, verify=False)
                else:
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
                headers={"Content-Type": "application/json"},
                auth=auth,
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201) or (
                res.status_code == 400
                and "resource_already_exists_exception" in res.text
            ):
                logger.info(f"Elasticsearch index '{idx}' is ready")
                return True
            logger.warning(
                f"Failed to create index '{idx}': {res.status_code} {res.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index {idx}: {e}")
            return False

    def import_dashboards_bundle(self) -> bool:
        """Imports Kibana saved objects bundle from NDJSON seed file."""
        dash_url = self._get_dashboard_url()
        if not dash_url:
            return False

        ndjson_path = os.path.join(
            ELASTICSEARCH_SEED_DIR, "dashboards", "dashboards_export.ndjson"
        )
        if not os.path.isfile(ndjson_path):
            logger.warning(f"Dashboards NDJSON file not found at {ndjson_path}")
            return False

        base_prefix = self._get_base_index_prefix()
        try:
            with open(ndjson_path, "r", encoding="utf-8") as f:
                content = f.read()

            if base_prefix != "nxguard_trn":
                content = content.replace('"nxguard_trn', f'"{base_prefix}')

            files = {
                "file": (
                    "dashboards_export.ndjson",
                    content.encode("utf-8"),
                    "application/ndjson",
                )
            }
            res = requests.post(
                f"{dash_url}/api/saved_objects/_import?overwrite=true",
                headers={"kbn-xsrf": "true"},
                files=files,
                auth=self._get_dashboard_auth(),
                timeout=10,
                verify=False,
            )
            if res.status_code in (200, 201):
                logger.info(
                    f"Kibana dashboards bundle imported successfully at {dash_url}"
                )
                return True
            logger.warning(
                f"Kibana _import returned status {res.status_code}: {res.text}"
            )
            return False
        except Exception as e:
            logger.warning(f"Failed to import Kibana bundle: {e}")
            return False

    def create_data_view(self, pattern_title: Optional[str] = None) -> bool:
        """Creates a Data View in Kibana via the Data Views API."""
        dash_url = self._get_dashboard_url()
        if not dash_url:
            return False

        base_prefix = self._get_base_index_prefix()
        title = pattern_title or f"{base_prefix}*"
        data_view_id = base_prefix

        payload = {
            "data_view": {
                "id": data_view_id,
                "name": title,
                "title": title,
                "timeFieldName": "logtime",
            }
        }
        try:
            res = requests.post(
                f"{dash_url}/api/data_views/data_view?override=true",
                json=payload,
                headers={"Content-Type": "application/json", "kbn-xsrf": "true"},
                auth=self._get_dashboard_auth(),
                timeout=5,
                verify=False,
            )
            if res.status_code in (200, 201, 409) or (
                res.status_code == 400 and "conflict" in res.text.lower()
            ):
                logger.info(f"Kibana Data View '{data_view_id}' is ready")
                return True
            logger.warning(f"Failed to create Data View: {res.status_code} {res.text}")
            return False
        except Exception as e:
            logger.warning(f"Error creating Data View: {e}")
            return False

    def ensure_structures(self, force: bool = False) -> bool:
        """Provisions index template, daily index, and Kibana dashboard objects."""
        if not self.is_configured():
            return False

        if not force and ElasticsearchSetupService._structures_initialized:
            return True

        logger.info(
            "Initializing Elasticsearch templates, indices, and Kibana objects..."
        )
        tmpl_ok = self.create_index_template()
        idx_ok = self.create_index_if_not_exists()
        self.setup_dashboard_user()
        dash_ok = self.import_dashboards_bundle()
        dv_ok = self.create_data_view()

        ElasticsearchSetupService._structures_initialized = True
        logger.info(
            f"Elasticsearch setup complete: template={tmpl_ok}, index={idx_ok}, data_view={dv_ok}, dashboards={dash_ok}"
        )
        return tmpl_ok and idx_ok
