from flask import Blueprint, make_response, Response

from nxcore.controllers.base_controller import (
    response_error_404
)

from api.model.acme_model import ChallengeDao

routes = Blueprint("acme", __name__)


@routes.route("/.well-known/acme-challenge/<key>", methods=["GET"])
@routes.route("/acme-challenge/<key>", methods=["GET"])
def get_config(key: str) -> Response:
    """
    Retrieve ACME challenge configuration for a given key.

    Args:
        key: The unique identifier for the ACME challenge

    Returns:
        Response: Plain text response with challenge content or 404 error
    """
    with ChallengeDao() as model:
        result = model.get_by_key(key)
        if result:
            response = make_response(result["content"], 200)
            response.mimetype = "text/plain"
            return response
        return response_error_404()
