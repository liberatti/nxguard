import datetime
import json

import config
from api.repository.redis_cache import RedisCache
from basic4web.common_utils import get_server_id


def update_node_status() -> None:
    if config.NXGUARD_ROLE == "main":
        with RedisCache() as cache:
            node = {
                "_id": get_server_id(),
                "status": "ACTIVE",
                "role": config.NXGUARD_ROLE,
                "last_contact": datetime.datetime.now(config.TZ),
                "scn": None
            }
            cache.persist(f"node_{get_server_id()}", json.dumps(node), expire=120)
