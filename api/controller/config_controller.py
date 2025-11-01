from flask import Blueprint, Response

from api.repository.redis_cache import RedisCache
from basic4web.controllers.base_controller import (
    response_data
)

routes = Blueprint("config", __name__)


@routes.route("/health", methods=["GET"])
def health() -> Response:
    r = dict()
    with RedisCache() as cache:
        r.update({"nodes": cache.get_items_by_prefix("node_*")})
    return response_data(r)
