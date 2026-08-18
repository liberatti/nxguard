from flask import Blueprint, Response
from nxcore.controllers.base_controller import (
    response_data,
    response_error,
    has_any_authority,
)
from nxcore.middleware.socket_manager import emit_event

import engine.admin as c_admin
import engine.build as c_builder
from api.model.config_model import ChangeDao, ConfigBackupDao
from api.model.upstream_model import NodeStatusDao

routes = Blueprint("config", __name__)


@routes.route("/health", methods=["GET"])
def health() -> Response:
    with NodeStatusDao() as node_dao:
        nodes = node_dao.get_active_nodes()
    with ChangeDao() as change_dao:
        changes = change_dao.get_all()
        changes_list = (
            [c["name"] for c in changes["data"]]
            if changes and "data" in changes
            else []
        )
    return response_data(
        {
            "nodes": nodes,
            "apply_pendding": changes_list,
            "changes": changes["data"] if changes and "data" in changes else [],
        }
    )


@routes.route("/changes", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get_changes() -> Response:
    with ChangeDao() as change_dao:
        changes = change_dao.get_all()
        return response_data(changes, change_dao.pageSchema)


@routes.route("/apply", methods=["GET", "POST"])
@has_any_authority(authorities=["superuser"])
def apply_config() -> Response:
    conf = c_builder.get_config()
    val = c_admin.validate(conf)
    if val and val.get("status") == "ok":
        cst = c_admin.apply(val["scn"])
        if cst and cst.get("status") == "ok":
            with ChangeDao() as change_dao:
                change_dao.delete_all()
            emit_event("tracking_aply")
            return response_data({"status": "ok", "scn": cst.get("scn")})
        else:
            return response_error(
                f"Failed to apply config: {cst.get('message') if cst else 'Unknown error'}"
            )
    else:
        return response_error(
            f"Failed to validate config: {val.get('message') if val else 'Unknown error'}"
        )


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def config() -> Response:
    with ConfigBackupDao() as backup_dao:
        latest = backup_dao.get_latest()
        r = latest["data"] if latest else None
    return response_data(r)
