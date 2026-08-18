import requests
from datetime import datetime
from typing import Dict, Any
from nxcore.middleware.logging_manager import logger
from api.model.config_model import ConfigDao
from marshmallow import EXCLUDE, Schema, fields
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema
import config


# Define Schemas
class FeedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    slug = fields.String()
    provider = fields.String()
    version = fields.String()
    type = fields.String()
    content = fields.List(fields.String())
    action = fields.String()
    scope = fields.String()
    source = fields.String()
    description = fields.String()
    update_interval = fields.String()
    updated_on = fields.DateTime(
        format=config.DATETIME_FMT, allow_none=True, required=False
    )


def _parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except Exception:
            pass
    return None


class FeedService:
    def __init__(self):
        self.schema = FeedSchema()
        page_class = type(
            "pagination",
            (Schema,),
            {
                "metadata": fields.Nested(PageMetaSchema, many=False),
                "data": fields.Nested(FeedSchema, many=True),
            },
        )
        self.pageSchema = page_class()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def json_load(self, json_data):
        return self.schema.load(json_data)

    def get_all(self, pagination=None):
        try:
            url, headers = IPXAService.get_api_config("/api/feed")
            params = {}
            if pagination:
                params = {
                    "page": pagination.get("page", 1),
                    "size": pagination.get("per_page", 10),
                }

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                if (
                    isinstance(res_data, dict)
                    and "data" in res_data
                    and isinstance(res_data["data"], list)
                ):
                    feeds = res_data["data"]
                    pagination_meta = res_data.get("metadata", {})
                else:
                    feeds = (
                        res_data.get("feeds", []) if isinstance(res_data, dict) else []
                    )
                    pag = (
                        res_data.get("pagination", {})
                        if isinstance(res_data, dict)
                        else {}
                    )
                    pagination_meta = {
                        "total_elements": pag.get("total", len(feeds)),
                        "page": pag.get("page", 1),
                        "per_page": pag.get("per_page", 10),
                    }

                mapped_feeds = []
                for f in feeds:
                    mapped_feeds.append(
                        {
                            "_id": str(f.get("_id") or f.get("id", "")),
                            "name": f.get("name"),
                            "slug": f.get("slug") or f.get("name"),
                            "type": f.get("type"),
                            "source": f.get("source") or f.get("url"),
                            "description": f.get("description"),
                            "provider": f.get("provider", "ipxa"),
                            "version": f.get("version", "1.0"),
                            "action": f.get("action", "deny"),
                            "scope": f.get("scope", "system"),
                            "update_interval": f.get("update_interval", "daily"),
                            "updated_on": _parse_dt(f.get("updated_on")),
                        }
                    )

                return {"metadata": pagination_meta, "data": mapped_feeds}
            return {
                "metadata": {"total_elements": 0, "page": 1, "per_page": 10},
                "data": [],
            }
        except Exception as e:
            logger.error(f"Error fetching feeds from IPXA: {e}")
            return {
                "metadata": {"total_elements": 0, "page": 1, "per_page": 10},
                "data": [],
            }

    def get_by_type(self, t):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed?type={t}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                if (
                    isinstance(res_data, dict)
                    and "data" in res_data
                    and isinstance(res_data["data"], list)
                ):
                    feeds = res_data["data"]
                elif isinstance(res_data, list):
                    feeds = res_data
                else:
                    feeds = (
                        res_data.get("feeds", []) if isinstance(res_data, dict) else []
                    )

                mapped_feeds = []
                for f in feeds:
                    content = f.get("content", [])
                    if isinstance(content, list):
                        data_str = "\n".join(str(x) for x in content)
                    else:
                        data_str = str(f.get("data", content or ""))

                    mapped_feeds.append(
                        {
                            "_id": str(f.get("_id") or f.get("id", "")),
                            "name": f.get("name"),
                            "slug": f.get("slug") or f.get("name"),
                            "type": f.get("type"),
                            "content": content,
                            "data": data_str,
                            "source": f.get("source") or f.get("url"),
                            "description": f.get("description"),
                            "provider": f.get("provider", "ipxa"),
                            "version": f.get("version", "1.0"),
                            "action": f.get("action", "deny"),
                            "scope": f.get("scope", "system"),
                            "update_interval": f.get("update_interval", "daily"),
                            "updated_on": _parse_dt(f.get("updated_on")),
                        }
                    )

                return mapped_feeds
            return []
        except Exception as e:
            logger.error(f"Error fetching feeds by type from IPXA: {e}")
            return []

    def get_by_id(self, _id):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed/{_id}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                f_data = response.json()
                f = f_data.get("data", f_data) if isinstance(f_data, dict) else f_data
                if isinstance(f, dict):
                    return {
                        "_id": str(f.get("_id") or f.get("id", "")),
                        "name": f.get("name"),
                        "slug": f.get("slug") or f.get("name"),
                        "type": f.get("type"),
                        "source": f.get("source") or f.get("url"),
                        "description": f.get("description"),
                        "provider": f.get("provider", "ipxa"),
                        "version": f.get("version", "1.0"),
                        "action": f.get("action", "deny"),
                        "scope": f.get("scope", "system"),
                        "update_interval": f.get("update_interval", "daily"),
                        "updated_on": _parse_dt(f.get("updated_on")),
                    }
            return None
        except Exception as e:
            logger.error(f"Error fetching feed by ID from IPXA: {e}")
            return None

    def persist(self, vo):
        try:
            url, headers = IPXAService.get_api_config("/api/feed/")
            ipxa_feed = {
                "name": vo.get("name"),
                "slug": vo.get("slug") or vo.get("name"),
                "provider": vo.get("provider", "ipxa"),
                "type": vo.get("type"),
                "source": vo.get("source") or vo.get("url"),
                "description": vo.get("description"),
                "format": vo.get("format", "list"),
                "update_interval": vo.get("update_interval", "daily"),
            }
            response = requests.post(url, headers=headers, json=ipxa_feed, timeout=5)
            if response.status_code in [200, 201]:
                res = response.json()
                res_dict = res.get("data", res) if isinstance(res, dict) else {}
                return str(res_dict.get("_id") or res_dict.get("id", ""))
            return None
        except Exception as e:
            logger.error(f"Error persisting feed to IPXA: {e}")
            return None

    def update_by_id(self, _id, vo):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed/{_id}")
            ipxa_feed = {
                "name": vo.get("name"),
                "slug": vo.get("slug") or vo.get("name"),
                "provider": vo.get("provider", "ipxa"),
                "type": vo.get("type"),
                "source": vo.get("source") or vo.get("url"),
                "description": vo.get("description"),
                "format": vo.get("format", "list"),
                "update_interval": vo.get("update_interval", "daily"),
            }
            response = requests.put(url, headers=headers, json=ipxa_feed, timeout=5)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error updating feed on IPXA: {e}")
            return False

    def delete_by_id(self, _id):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed/{_id}")
            response = requests.delete(url, headers=headers, timeout=5)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error deleting feed on IPXA: {e}")
            return False


class IPXAService:
    feeds = FeedService()

    @classmethod
    def get_api_config(cls, path=""):
        url = None
        key = None
        try:
            with ConfigDao() as dao:
                conf = dao.get_active()
                if conf and "ipxa" in conf:
                    ipxa_conf = conf["ipxa"]
                    url = ipxa_conf.get("url")
                    key = ipxa_conf.get("key")
        except Exception as e:
            logger.debug(f"Could not read IPXA config from database: {e}")

        if url and not url.startswith("http"):
            url = f"http://{url}"

        if url:
            url = url.rstrip("/")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["x-api-key"] = key

        return f"{url}{path}", headers

    @classmethod
    def geo_info(cls, ip: str) -> dict:
        ip_info = {}
        try:
            url, headers = cls.get_api_config(f"/api/ip/info/{ip}")
            logger.debug(f"Fetching GeoIP info from IPXA: {url}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                res_data = response.json()
                data = (
                    res_data.get("data", res_data) if isinstance(res_data, dict) else {}
                )
                loc = data.get("location", {})
                org = data.get("organization", {})
                asn_number = org.get("asn_number")

                ip_info.update(
                    {
                        "country": loc.get("country_code"),
                        "ans_number": (
                            str(asn_number) if asn_number is not None else None
                        ),
                        "organization": org.get("asn_name")
                        or org.get("asn_description"),
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    }
                )

                ip_data = data.get("ip", {})
                network = ip_data.get("network")
                prefix = ip_data.get("prefix")
                if network is not None and prefix is not None:
                    from api.tools.network_tool import NetworkTool

                    try:
                        r = NetworkTool.range_from_network(f"{network}/{prefix}")
                        ip_info.update(
                            {
                                "net_start": r.get("net_start"),
                                "net_end": r.get("net_end"),
                            }
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to query GeoIP from IPXA: {e}")
        return ip_info

    @classmethod
    def rbl_check(cls, ip: str, sensor: Dict[str, Any] = None) -> Dict[str, bool]:
        try:
            url, headers = cls.get_api_config(f"/api/ip/check/{ip}")
            logger.debug(f"Checking IP block status on IPXA: {url}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                res_data = response.json()
                data = (
                    res_data.get("data", res_data) if isinstance(res_data, dict) else {}
                )
                risk_score = data.get("risk_score", 0)
                reasons = data.get("reasons", [])
                blocked = (risk_score >= 5) or len(reasons) > 0
                return {"blocked": blocked}
            return {"blocked": False}
        except Exception as e:
            logger.error(f"Error checking IP in IPXA RBL: {e}")
            return {"blocked": False}
