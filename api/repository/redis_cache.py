import config
from nxcore.repository.redis_base_dao import RedisDAO


class RedisCache(RedisDAO):

    def __init__(self):
        super().__init__(
            host=config.REDIS_CACHE_HOST,
            port=config.REDIS_CACHE_PORT
        )
