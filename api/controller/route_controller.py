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

from api.model.route_model import RouteDao

routes = Blueprint("route", __name__)


@routes.route("/<route_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(route_id: str) -> Response:
    with RouteDao() as dao:
        route = dao.get_by_id(route_id)
        return response_data(route, dao.schema) if route else response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    try:
        with RouteDao() as dao:
            route_dict = dao.json_load(request.json)
            pk = dao.persist(route_dict)
            route = dao.get_by_id(pk)
            return response_data(route, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    service_id = request.args.get("service_id")
    with RouteDao() as dao:
        if service_id:
            rows = dao.get_all_by_service_id(service_id)
            return response_data(rows)
        pagination = get_pagination()
        result = dao.get_all(pagination=pagination)
        return response_data(result, dao.pageSchema)


@routes.route("/<route_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(route_id: str) -> Response:
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
    with RouteDao() as dao:
        result = dao.delete_by_id(route_id)
        return response_data_removed(route_id) if result else response_error_404()
