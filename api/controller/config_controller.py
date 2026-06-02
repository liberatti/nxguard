from nxcore.controllers.base_controller import response_data
from flask import Blueprint, Response

import engine.build as c_build
from api.model.upstream_model import NodeStatusDao

routes = Blueprint("config", __name__)


@routes.route("/health", methods=["GET"])
def health() -> Response:
    with NodeStatusDao() as node_dao:
        nodes = node_dao.get_active_nodes()
    return response_data({"nodes": nodes})


@routes.route("", methods=["GET"])
def config() -> Response:
    r = c_build.read_from_json("config.json")
    return response_data(r)
