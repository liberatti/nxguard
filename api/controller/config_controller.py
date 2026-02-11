import json

from basic4web.controllers.base_controller import response_data
from flask import Blueprint, Response

import engine.build as c_build
from config import cache_db

routes = Blueprint("config", __name__)


@routes.route("/health", methods=["GET"])
def health() -> Response:
    nodes = []

    for key in cache_db.smembers("idx:nodes"):
        val = cache_db.get(key)
        if val:
            node = json.loads(val)
            node.update({"_id": key})
            nodes.append(node)
        else:
            cache_db.srem("idx:nodes", key)
    return response_data({"nodes": nodes})


@routes.route("", methods=["GET"])
def config() -> Response:
    r = c_build.read_from_json("active.json")
    return response_data(r)
