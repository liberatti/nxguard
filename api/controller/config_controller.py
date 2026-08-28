import json
from flask import Blueprint, Response, request
from marshmallow import ValidationError
from nxcore.controllers.base_controller import (
    response_data,
    response_error,
    response_error_parse,
    has_any_authority,
)
from nxcore.middleware.socket_manager import emit_event
from nxcore.middleware.logging_manager import logger

import engine.admin as c_admin
import engine.build as c_builder
from api.model.config_model import ChangeDao, ConfigDao
from api.model.upstream_model import NodeStatusDao

routes = Blueprint("config", __name__)


@routes.after_request
def after(response: Response) -> Response:
    if (
        request.method
        in [
            "PUT",
            "POST",
            "DELETE",
            "PATCH",
        ]
        and response.status_code in [200, 201]
        and not request.path.endswith("/apply")
    ):
        with ChangeDao() as dao:
            if not dao.get_by_name("config"):
                dao.persist({"name": "config"})
            emit_event("tracking_evt")
    return response


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
@has_any_authority(authorities=["superuser"])
def config() -> Response:
    with ConfigDao() as dao:
        return response_data(dao.get_active(), dao.schema)


@routes.route("", methods=["PUT"])
@routes.route("/<_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(_id=None) -> Response:
    try:
        with ConfigDao() as dao:
            active = dao.get_active()
            conf_id = _id or (active["_id"] if active else 1)
            config_dict = dao.json_load(request.json)
            dao.update_by_id(conf_id, config_dict)
            return response_data(dao.get_active(), dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/backup", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def backup_export() -> Response:
    conf = c_builder.get_config()
    upstreams = []
    for u in conf.get("upstreams", []):
        u_copy = dict(u)
        u_copy.pop("healthy", None)
        if "targets" in u_copy and isinstance(u_copy["targets"], list):
            clean_targets = []
            for t in u_copy["targets"]:
                if isinstance(t, dict):
                    t_copy = dict(t)
                    t_copy.pop("healthy", None)
                    clean_targets.append(t_copy)
                else:
                    clean_targets.append(t)
            u_copy["targets"] = clean_targets
        upstreams.append(u_copy)

    export_data = {
        "config": conf.get("config", {}),
        "certificates": conf.get("certificates", []),
        "sensors": conf.get("sensors", []),
        "upstreams": upstreams,
        "services": conf.get("services", []),
    }
    return Response(
        json.dumps(
            export_data,
            indent=2,
            default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o),
        ),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=init-data.json"},
    )


@routes.route("/backup", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def backup_import() -> Response:
    try:
        if "file" in request.files:
            uploaded_file = request.files["file"]
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)
        elif "jsonfile" in request.files:
            uploaded_file = request.files["jsonfile"]
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)
        elif "zipfile" in request.files:
            uploaded_file = request.files["zipfile"]
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)
        elif request.is_json:
            data = request.get_json()
        else:
            return response_error("No JSON configuration file provided")

        c_builder.init_from_data(data=data)
        with ChangeDao() as dao:
            if not dao.get_by_name("config"):
                dao.persist({"name": "config"})
            emit_event("tracking_evt")
        return response_data(
            {"status": "ok", "message": "Configuration imported successfully"}
        )
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        return response_error(f"Failed to import configuration: {str(e)}")
