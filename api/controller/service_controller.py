from flask import Blueprint, request, Response
from marshmallow import ValidationError

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    response_error_parse,
    response_ok,
    response_error,
    get_pagination,
    has_any_authority,
    response_data_removed,
)

from nxcore.common_utils import (
    deep_merge,
)
from nxcore.middleware.socket_manager import emit_event
from api.model.config_model import ChangeDao
from api.model.service_model import ServiceDao

routes = Blueprint("service", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after service modifications.

    Args:
        response: The Flask response object

    Returns:
        Response: The modified response object
    """
    if request.method in [
        "PUT",
        "POST",
        "DELETE",
        "PATCH",
    ] and response.status_code in [200, 201]:
        with ChangeDao() as dao:
            if not dao.get_by_name("service"):
                dao.persist({"name": "service"})
            emit_event("tracking_evt")
    return response


@routes.route("/<service_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(service_id: str) -> Response:
    """
    Retrieve a specific service by ID.

    Args:
        service_id: The unique identifier of the service

    Returns:
        Response: JSON response containing the service data or 404 error
    """
    with ServiceDao() as dao:
        service = dao.get_by_id(service_id)
        return response_data(service, dao.schema) if service else response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new service.
    Checks if the domains (SANS) are already in use before creating.

    Returns:
        Response: JSON response containing the created service or error message
    """
    try:
        with ServiceDao() as dao:
            service_dict = dao.json_load(request.json)
            sv_check = dao.get_by_sans(service_dict["sans"])
            if sv_check:
                return response_error("Domains in use", code=406)

            pk = dao.persist(service_dict)
            service = dao.get_by_id(pk)
            return response_data(service, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all services.

    Returns:
        Response: JSON response containing paginated service list or 404 error
    """
    query = (
        request.args.get("query")
        or request.args.get("q")
        or request.args.get("name")
        or request.args.get("search")
    )
    with ServiceDao() as dao:
        result = dao.search(query=query, pagination=get_pagination())
        return (
            response_data(result, dao.pageSchema)
            if result["metadata"]["total_elements"] > 0
            else response_error_404()
        )


@routes.route("/<service_id>", methods=["PATCH"])
@has_any_authority(authorities=["superuser"])
def partial_update(service_id: str) -> Response:
    """
    Partially update a service with specific fields.

    Args:
        service_id: The unique identifier of the service to update

    Returns:
        Response: Success message or error response
    """
    try:
        with ServiceDao() as dao:
            service_new = dao.json_load(request.json)
            service_old = dao.get_by_id(service_id)
            dao.update_by_id(service_id, deep_merge(service_old, service_new))
            return response_ok("Partially updated")
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<service_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(service_id: str) -> Response:
    """
    Update an existing service.
    Checks if the domains (SANS) are already in use before updating.

    Args:
        service_id: The unique identifier of the service to update

    Returns:
        Response: JSON response containing the updated service or error message
    """
    try:
        with ServiceDao() as dao:
            service_dict = dao.json_load(request.json)
            sv_check = dao.get_by_sans(service_dict["sans"])
            if sv_check and str(service_id) != str(sv_check["_id"]):
                return response_error("Domains in use", code=406)

            dao.update_by_id(service_id, service_dict)
            return response_data(dao.get_by_id(service_id), dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<service_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(service_id: str) -> Response:
    """
    Delete a service.

    Args:
        service_id: The unique identifier of the service to delete

    Returns:
        Response: Success message or error response
    """
    with ServiceDao() as dao:
        result = dao.delete_by_id(service_id)
        return response_data_removed(service_id) if result else response_error_404()
