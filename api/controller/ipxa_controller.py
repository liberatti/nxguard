from flask import Blueprint, Response

from api.middleware.controllers.base_controller import (
    response_data,
    response_error_404,
    has_any_authority,
)
from api.services.feed_service import FeedService

routes = Blueprint("ipxa", __name__)


@routes.route("/stats", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def stats() -> Response:
    """
    Retrieve IPXA statistics.

    Returns:
        Response: JSON response containing IPXA stats or 404 error
    """
    with FeedService() as feed_service:
        data = feed_service.get_stats()
        return (
            response_data(data)
            if data and isinstance(data, dict)
            else response_error_404()
        )
