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


class JailEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    ipaddr = fields.String()
    banned_on = fields.DateTime(
        format=config.DATETIME_FMT, allow_none=True, required=False
    )


class JailRulesSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    field = fields.String()
    regex = fields.String()


class JailSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    bantime = fields.Integer()
    occurrence = fields.Integer()
    interval = fields.Integer()
    content = fields.Nested(JailEntrySchema, many=True)
    rules = fields.Nested(JailRulesSchema, many=True)


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

    def json_load(self, json_data):
        return self.schema.load(json_data)

    def get_all(self, pagination=None):
        try:
            url, headers = IPXAService.get_api_config("/api/feed")
            params = {}
            if pagination:
                params["page"] = pagination.get("page", 1)
                params["per_page"] = pagination.get("per_page", 10)

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                feeds = res_data.get("feeds", [])

                mapped_feeds = []
                for f in feeds:
                    mapped_feeds.append(
                        {
                            "_id": str(f.get("id", "")),
                            "name": f.get("name"),
                            "slug": f.get("name"),
                            "type": f.get("type"),
                            "source": f.get("url"),
                            "description": f.get("description"),
                            "provider": f.get("provider", "ipxa"),
                            "version": f.get("version", "1.0"),
                            "action": f.get("action", "deny"),
                            "scope": f.get("scope", "system"),
                            "update_interval": f.get("update_interval", "daily"),
                            "updated_on": f.get("updated_on"),
                        }
                    )

                pag = res_data.get("pagination", {})
                total = pag.get("total", len(mapped_feeds))

                pagination_meta = {
                    "total_elements": total,
                    "page": pag.get("page", 1),
                    "per_page": pag.get("per_page", 10),
                }

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

    def get_by_id(self, _id):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed/{_id}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                f = response.json()
                return {
                    "_id": str(f.get("id", "")),
                    "name": f.get("name"),
                    "slug": f.get("name"),
                    "type": f.get("type"),
                    "source": f.get("url"),
                    "description": f.get("description"),
                    "provider": f.get("provider", "ipxa"),
                    "version": f.get("version", "1.0"),
                    "action": f.get("action", "deny"),
                    "scope": f.get("scope", "system"),
                    "update_interval": f.get("update_interval", "daily"),
                    "updated_on": f.get("updated_on"),
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching feed by ID from IPXA: {e}")
            return None

    def persist(self, vo):
        try:
            url, headers = IPXAService.get_api_config("/api/feed")
            ipxa_feed = {
                "name": vo.get("name"),
                "type": vo.get("type"),
                "url": vo.get("source"),
                "description": vo.get("description"),
            }
            response = requests.post(url, headers=headers, json=ipxa_feed, timeout=5)
            if response.status_code in [200, 201]:
                res = response.json()
                return str(res.get("id", ""))
            return None
        except Exception as e:
            logger.error(f"Error persisting feed to IPXA: {e}")
            return None

    def update_by_id(self, _id, vo):
        try:
            url, headers = IPXAService.get_api_config(f"/api/feed/{_id}")
            ipxa_feed = {
                "name": vo.get("name"),
                "type": vo.get("type"),
                "url": vo.get("source"),
                "description": vo.get("description"),
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


class JailService:
    def __init__(self):
        self.schema = JailSchema()
        page_class = type(
            "pagination",
            (Schema,),
            {
                "metadata": fields.Nested(PageMetaSchema, many=False),
                "data": fields.Nested(JailSchema, many=True),
            },
        )
        self.pageSchema = page_class()

    def json_load(self, json_data):
        return self.schema.load(json_data)

    def get_all(self, pagination=None):
        try:
            url, headers = IPXAService.get_api_config("/api/jail")
            params = {}
            if pagination:
                params["page"] = pagination.get("page", 1)
                params["per_page"] = pagination.get("per_page", 10)

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                jails = res_data.get("jails", [])
                mapped_jails = []
                for j in jails:
                    mapped_jails.append(
                        {
                            "_id": str(j.get("id", "")),
                            "name": j.get("name"),
                            "bantime": j.get("bantime"),
                            "occurrence": j.get("occurrence"),
                            "interval": j.get("interval"),
                            "content": j.get("content", []),
                            "rules": j.get("rules", []),
                        }
                    )

                pag = res_data.get("pagination", {})
                total = pag.get("total", len(mapped_jails))

                pagination_meta = {
                    "total_elements": total,
                    "page": pag.get("page", 1),
                    "per_page": pag.get("per_page", 10),
                }

                return {"metadata": pagination_meta, "data": mapped_jails}
            return {
                "metadata": {"total_elements": 0, "page": 1, "per_page": 10},
                "data": [],
            }
        except Exception as e:
            logger.error(f"Error fetching jails from IPXA: {e}")
            return {
                "metadata": {"total_elements": 0, "page": 1, "per_page": 10},
                "data": [],
            }

    def get_by_id(self, _id):
        try:
            url, headers = IPXAService.get_api_config(f"/api/jail/{_id}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                j = response.json()
                return {
                    "_id": str(j.get("id", "")),
                    "name": j.get("name"),
                    "bantime": j.get("bantime"),
                    "occurrence": j.get("occurrence"),
                    "interval": j.get("interval"),
                    "content": j.get("content", []),
                    "rules": j.get("rules", []),
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching jail by ID from IPXA: {e}")
            return None

    def persist(self, vo: Dict[str, Any]) -> str:
        try:
            from nxcore.common_utils import replace_tz

            default_date = replace_tz(datetime.now()).replace(microsecond=0)
            if "content" in vo:
                for c in vo["content"]:
                    if "banned_on" not in c:
                        c.update(
                            {
                                "banned_on": (
                                    default_date.isoformat()
                                    if hasattr(default_date, "isoformat")
                                    else str(default_date)
                                )
                            }
                        )

            url, headers = IPXAService.get_api_config("/api/jail")
            ipxa_jail = {
                "name": vo.get("name"),
                "bantime": vo.get("bantime"),
                "occurrence": vo.get("occurrence"),
                "interval": vo.get("interval"),
                "content": vo.get("content", []),
                "rules": vo.get("rules", []),
            }
            response = requests.post(url, headers=headers, json=ipxa_jail, timeout=5)
            if response.status_code in [200, 201]:
                res = response.json()
                return str(res.get("id", ""))
            return None
        except Exception as e:
            logger.error(f"Error persisting jail to IPXA: {e}")
            return None

    def update_by_id(self, _id, vo):
        try:
            url, headers = IPXAService.get_api_config(f"/api/jail/{_id}")
            ipxa_jail = {
                "name": vo.get("name"),
                "bantime": vo.get("bantime"),
                "occurrence": vo.get("occurrence"),
                "interval": vo.get("interval"),
                "content": vo.get("content", []),
                "rules": vo.get("rules", []),
            }
            response = requests.put(url, headers=headers, json=ipxa_jail, timeout=5)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error updating jail on IPXA: {e}")
            return False

    def delete_by_id(self, _id):
        try:
            url, headers = IPXAService.get_api_config(f"/api/jail/{_id}")
            response = requests.delete(url, headers=headers, timeout=5)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error deleting jail from IPXA: {e}")
            return False


class IPXAService:
    feeds = FeedService()
    jails = JailService()

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
            url, headers = cls.get_api_config(f"/api/ip/info/{ip}?wid=2")
            logger.debug(f"Fetching GeoIP info from IPXA: {url}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                data = response.json()
                loc = data.get("location", {})
                org = data.get("organization", {})
                asn_number = org.get("asn_number")

                ip_info.update(
                    {
                        "country": loc.get("country_code"),
                        "ans_number": (
                            str(asn_number) if asn_number is not None else None
                        ),
                        "organization": org.get("asn_name"),
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
                data = response.json()
                risk_score = data.get("risk_score", 0)
                reasons = data.get("reasons", [])
                blocked = (risk_score >= 5) or len(reasons) > 0
                return {"blocked": blocked}
            return {"blocked": False}
        except Exception as e:
            logger.error(f"Error checking IP in IPXA RBL: {e}")
            return {"blocked": False}
