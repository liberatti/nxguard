import json
from flask import Blueprint, Response

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    has_any_authority,
    response_error_500,
)
from api.model.config_model import ConfigDao, ConfigBackupDao

routes = Blueprint("replica", __name__)


@routes.route("/scn", methods=["GET"])
@has_any_authority(_internal=True)
def scn() -> Response:
    """
    Retrieve the System Change Number (SCN) from the active configuration.

    Returns:
        Response: JSON response containing the SCN or error response
    """
    with ConfigDao() as dao:
        active = dao.get_active()
        if active and "active_scn" in active:
            return response_data({"scn": active["active_scn"]})
    return response_error_500("System not ready")


@routes.route("/config", methods=["GET"])
@has_any_authority(_internal=True)
def config() -> Response:
    """
    Retrieve the active cluster configuration.

    Returns:
        Response: JSON response containing the cluster configuration
    """
    with ConfigBackupDao() as backup_dao:
        latest = backup_dao.get_latest()
        if latest and "data" in latest:
            r = latest["data"]
            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except Exception:
                    pass
            return response_data(r)
    return response_error_404()
