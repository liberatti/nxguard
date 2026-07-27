import requests
from datetime import datetime
from typing import Dict, Any, List

from nxcore.common_utils import replace_tz
from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


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


class JailDao(DuckDAO):
    """
    DAO for managing jail data via external IPXA API.
    """

    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="jail", schema=JailSchema)

    def create_schema(self):
        # Local table is no longer needed since it consumes IPXA API
        pass

    def _get_api_headers(self):
        from api.tools.feed_service import SecurityFeedService

        _, key = SecurityFeedService.get_ipxa_config()
        headers = {"Content-Type": "application/json"}
        if key:
            headers["x-api-key"] = key
        return headers

    def _get_api_url(self, path=""):
        from api.tools.feed_service import SecurityFeedService

        url, _ = SecurityFeedService.get_ipxa_config()
        return f"{url}/api/jail{path}"

    def get_all(self, pagination=None, order_by=None):
        try:
            url = self._get_api_url()
            params = {}
            if pagination:
                params["page"] = pagination.get("page", 1)
                params["per_page"] = pagination.get("per_page", 10)

            response = requests.get(
                url, headers=self._get_api_headers(), params=params, timeout=5
            )
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
            url = self._get_api_url(f"/{_id}")
            response = requests.get(url, headers=self._get_api_headers(), timeout=5)
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

    def get_by_type(self, t: str) -> List[Dict[str, Any]]:
        try:
            url = self._get_api_url()
            response = requests.get(
                url, headers=self._get_api_headers(), params={"type": t}, timeout=5
            )
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
                return mapped_jails
            return []
        except Exception as e:
            logger.error(f"Error fetching jails by type from IPXA: {e}")
            return []

    def persist(self, vo: Dict[str, Any]) -> str:
        try:
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

            url = self._get_api_url()
            ipxa_jail = {
                "name": vo.get("name"),
                "bantime": vo.get("bantime"),
                "occurrence": vo.get("occurrence"),
                "interval": vo.get("interval"),
                "content": vo.get("content", []),
                "rules": vo.get("rules", []),
            }
            response = requests.post(
                url, headers=self._get_api_headers(), json=ipxa_jail, timeout=5
            )
            if response.status_code in [200, 201]:
                res = response.json()
                return str(res.get("id", ""))
            return None
        except Exception as e:
            logger.error(f"Error persisting jail to IPXA: {e}")
            return None

    def update_by_id(self, _id, vo):
        try:
            url = self._get_api_url(f"/{_id}")
            ipxa_jail = {
                "name": vo.get("name"),
                "bantime": vo.get("bantime"),
                "occurrence": vo.get("occurrence"),
                "interval": vo.get("interval"),
                "content": vo.get("content", []),
                "rules": vo.get("rules", []),
            }
            response = requests.put(
                url, headers=self._get_api_headers(), json=ipxa_jail, timeout=5
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error updating jail on IPXA: {e}")
            return False

    def delete_by_id(self, _id):
        try:
            url = self._get_api_url(f"/{_id}")
            response = requests.delete(url, headers=self._get_api_headers(), timeout=5)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error deleting jail from IPXA: {e}")
            return False

    def delete_all(self):
        return True
