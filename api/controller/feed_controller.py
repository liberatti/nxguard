from flask import Blueprint, request, Response

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    get_pagination,
    has_any_authority,
)

from api.services.ipxa_services import IPXAService

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
    feed = IPXAService.feeds.get_by_id(feed_id)
    return (
        response_data(feed, schema=IPXAService.feeds.schema)
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
    feed_type = request.args.get("type", type=str)
    if feed_type:
        feeds = IPXAService.feeds.get_by_type(feed_type)
    else:
        reputation_feeds = IPXAService.feeds.get_by_type("reputation") or []
        bypass_feeds = IPXAService.feeds.get_by_type("bypass") or []
        feeds = reputation_feeds + bypass_feeds

    pagination = get_pagination()
    page = pagination.get("page", 1) if pagination else 1
    per_page = pagination.get("per_page", 10) if pagination else 10

    result = {
        "metadata": {
            "total_elements": len(feeds),
            "page": page,
            "per_page": per_page,
        },
        "data": feeds,
    }
    return response_data(result, IPXAService.feeds.pageSchema)
