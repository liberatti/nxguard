import json

from basic4web.controllers.base_controller import response_data
from basic4web.middleware.logging import logger
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
            logger.info(f"{key}:{val}")
            node = json.loads(val)
            node.update({"_id": key})
            if val is None:
                cache_db.srem("idx:nodes", key)  # limpa índice morto
                continue
    return response_data({"nodes": nodes})


@routes.route("", methods=["GET"])
def config() -> Response:
    r = c_build.read_from_json("active.json")
    return response_data(r)
