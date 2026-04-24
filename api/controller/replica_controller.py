from flask import Blueprint, Response

from api.core.controllers.base_controller import (
    response_data,
    has_any_authority,
    response_error_500
)

from api.tools.cluster_tool import ClusterTool

routes = Blueprint("replica", __name__)


@routes.route("/scn", methods=["GET"])
@has_any_authority(_internal=True)
def scn() -> Response:
    """
    Retrieve the System Change Number (SCN) from the cluster configuration.

    Returns:
        Response: JSON response containing the SCN or error response
    """
    if not ClusterTool.CONFIG:
        return response_error_500("System not ready")
    return response_data({'scn': ClusterTool.CONFIG['scn']})


@routes.route("/config", methods=["GET"])
@has_any_authority(_internal=True)
def config() -> Response:
    """
    Retrieve the cluster configuration.

    Returns:
        Response: JSON response containing the cluster configuration
    """
    return response_data(ClusterTool.CONFIG)
