from flask import Blueprint, request, Response
from marshmallow import ValidationError

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    response_error_parse,
    get_pagination,
    has_any_authority,
    response_data_removed,
)
from nxcore.middleware.socket_manager import emit_event
from api.model.config_model import ChangeDao
from api.model.route_model import RouteDao, RouteSchema

routes = Blueprint("route", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after route modifications.
    """
    if request.method in [
        "PUT",
        "POST",
        "DELETE",
        "PATCH",
    ] and response.status_code in [200, 201]:
        with ChangeDao() as dao:
            if not dao.get_by_name("route"):
                dao.persist({"name": "route"})
            emit_event("tracking_evt")
    return response


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list routes.
    If service_id parameter is provided, returns all routes for that service.
    """
    service_id = request.args.get("service_id")
    with RouteDao() as dao:
        if service_id:
            results = dao.get_all_by_service_id(service_id)
            return response_data(results, RouteSchema(many=True))
        result = dao.get_all(pagination=get_pagination())
        return (
            response_data(result, dao.pageSchema)
            if result["metadata"]["total_elements"] > 0
            else response_error_404()
        )


@routes.route("/<route_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(route_id: str) -> Response:
    """
    Retrieve a specific route by ID.
    """
    with RouteDao() as dao:
        route = dao.get_by_id(route_id)
        return response_data(route, dao.schema) if route else response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new route.
    """
    try:
        with RouteDao() as dao:
            route_dict = dao.json_load(request.json)
            pk = dao.persist(route_dict)
            route = dao.get_by_id(pk)
            return response_data(route, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<route_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(route_id: str) -> Response:
    """
    Update an existing route.
    """
    try:
        with RouteDao() as dao:
            route_dict = dao.json_load(request.json)
            dao.update_by_id(route_id, route_dict)
            return response_data(dao.get_by_id(route_id), dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<route_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(route_id: str) -> Response:
    """
    Delete a route.
    """
    with RouteDao() as dao:
        result = dao.delete_by_id(route_id)
        return response_data_removed(route_id) if result else response_error_404()
