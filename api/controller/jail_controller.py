from flask import Blueprint, request, Response
from marshmallow import ValidationError

from api.core.controllers.base_controller import (
    response_data,
    response_error_404,
    response_error_parse,
    response_ok,
    get_pagination,
    has_any_authority,
    response_data_removed
)

from api.core.middleware.socket_manager import emit_event
from api.model.config_model import ChangeDao
from api.model.jail_model import JailDao

routes = Blueprint("jail", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after jail modifications.

    Args:
        response: The Flask response object

    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("jail"):
            dao.persist({"name": "jail"})
        emit_event("tracking_evt")
    return response


@routes.route("/<jail_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(jail_id: str) -> Response:
    """
    Retrieve a specific jail by ID.

    Args:
        jail_id: The unique identifier of the jail

    Returns:
        Response: JSON response containing the jail data or 404 error
    """
    dao = JailDao()
    jail = dao.get_by_id(jail_id)
    return response_data(jail, schema=dao.schema) if jail else response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save() -> Response:
    """
    Create a new jail.

    Returns:
        Response: JSON response containing the created jail or error message
    """
    dao = JailDao()
    try:
        jail_dict = dao.json_load(request.json)
        pk = dao.persist(jail_dict)
        jail = dao.get_by_id(pk)
        return response_data(jail, schema=dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all jails.

    Returns:
        Response: JSON response containing paginated jail list or 404 error
    """
    dao = JailDao()
    result = dao.get_all(pagination=get_pagination())
    return response_data(result, schema=dao.pageSchema) if result["metadata"]["total_elements"] > 0 else response_error_404()


@routes.route("/<jail_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(jail_id: str) -> Response:
    """
    Update an existing jail.

    Args:
        jail_id: The unique identifier of the jail to update

    Returns:
        Response: JSON response containing the updated jail or error message
    """
    dao = JailDao()
    try:
        jail_dict = dao.json_load(request.json)
        result = dao.update_by_id(jail_id, jail_dict)
        return response_data(result, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<jail_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(jail_id: str) -> Response:
    """
    Delete a jail.

    Args:
        jail_id: The unique identifier of the jail to delete

    Returns:
        Response: Success message or error response
    """
    dao = JailDao()
    result = dao.delete_by_id(jail_id)
    return response_data_removed(jail_id) if result else response_error_404()


@routes.route("/<jail_id>/add/<addr>", methods=["PUT"])
@has_any_authority(["superuser"])
def add_to_jail(jail_id: str, addr: str) -> Response:
    """
    Add an IP address to a jail.

    Args:
        jail_id: The unique identifier of the jail
        addr: The IP address to add

    Returns:
        Response: Success message or error response
    """
    dao = JailDao()
    try:
        result = dao.get_by_id(jail_id)
        result["content"].append({"ipaddr": addr})
        dao.update_by_id(jail_id, result)
        return response_ok("ok")
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<jail_id>/del/<addr>", methods=["PUT"])
@has_any_authority(["superuser"])
def del_to_jail(jail_id: str, addr: str) -> Response:
    """
    Remove an IP address from a jail.

    Args:
        jail_id: The unique identifier of the jail
        addr: The IP address to remove

    Returns:
        Response: Success message or error response
    """
    dao = JailDao()
    try:
        result = dao.get_by_id(jail_id)
        result["content"] = [content for content in result["content"] if addr not in content["ipaddr"]]
        dao.update_by_id(jail_id, result)
        return response_ok("ok")
    except ValidationError as err:
        return response_error_parse(err)
