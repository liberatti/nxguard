import datetime
import json

import config
import engine.admin as c_admin
from api.repository.redis_cache import RedisCache
from basic4web.common_utils import get_server_id


def update_node_status() -> None:
    if config.NXGUARD_ROLE == "main":
        with RedisCache() as cache:
            st = "ACTIVE" if c_admin.is_running() else "STOPPED"
            node = {
                "_id": get_server_id(),
                "status": st,
                "role": config.NXGUARD_ROLE,
                "last_check": datetime.datetime.now(config.TZ).isoformat(),
                "version": '',
                "net_recv": 0,
                "net_send": 0
            }
            cache.persist(f"node_{get_server_id()}", json.dumps(node), expire=120)
