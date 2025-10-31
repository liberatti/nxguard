from flask import Blueprint, Response

from basic4web.controllers.base_controller import (
    response_error_401
)

routes = Blueprint("config", __name__)


@routes.route("/health", methods=["GET"])
def health() -> Response:
    return response_error_401("Sign in failed")
