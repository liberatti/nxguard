from flask import Blueprint, request, Response

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    get_pagination,
    has_any_authority,
)

from api.services.feed_service import FeedService

routes = Blueprint("feed", __name__)


@routes.route("/<feed_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(feed_id: str) -> Response:
    """
    Retrieve a specific feed by ID.

    Args:
        feed_id: The unique identifier of the feed

    Returns:
        Response: JSON response containing the feed data or 404 error
    """
    with FeedService() as feed_service:
        feed = feed_service.get_by_id(feed_id)
        return (
            response_data(feed, schema=feed_service.schema)
            if feed
            else response_error_404()
        )


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list feeds.
    Uses get_by_type to retrieve 'reputation' for RBL Blocking and 'bypass' for RBL ByPass.

    Returns:
        Response: JSON response containing paginated feed list
    """
    feeds = []
    feed_type = request.args.get("type", type=str)
    with FeedService() as feed_service:
        if feed_type:
            feeds = feed_service.get_by_type(feed_type)
    page = {
        "data": feeds,
        "metadata": {
            "total_elements": len(feeds),
            "current_page": 1,
            "total_pages": 1,
        },
    }
    return response_data(page, feed_service.pageSchema)
