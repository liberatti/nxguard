from flask import Blueprint, request, Response
from marshmallow import ValidationError

from api.middleware.controllers.base_controller import (
    response_data,
    response_error_404,
    response_error_parse,
    response_data_removed,
    has_any_authority,
)

from api.repository.seclang_repository import RuleCategoryDao
from engine.seclang.seclang_schema import RuleCategorySchema

routes = Blueprint("rulecat", __name__)


@routes.route("/<cat_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(cat_id: str) -> Response:
    """
    Retrieve a specific rule category by ID.

    Args:
        cat_id: The unique identifier of the rule category

    Returns:
        Response: JSON response containing the rule category data or 404 error
    """
    with RuleCategoryDao() as dao:
        cat = dao.get_by_id(cat_id)
        if not cat:
            return response_error_404()
        return response_data(cat, dao.schema)


@routes.route("/by_name/<cat_name>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get_by_name(cat_name: str) -> Response:
    """
    Retrieve a rule category by name.

    Args:
        cat_name: The name of the rule category

    Returns:
        Response: JSON response containing the rule category data or 404 error
    """
    with RuleCategoryDao() as dao:
        cat = dao.get_by_name(cat_name)
        if not cat:
            return response_error_404()
        return response_data(cat, dao.schema)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search rule categories by name and phases.

    Returns:
        Response: JSON response containing the matching rule categories
    """
    name = request.args.get("name", type=str, default=None)
    phases_raw = request.args.getlist("phases")
    phases = []
    for p in phases_raw:
        for item in str(p).split(","):
            item = item.strip()
            if item.isdigit():
                phases.append(int(item))

    with RuleCategoryDao() as dao:
        if name and phases:
            result = dao.get_by_name_and_phases(name, phases)
        elif name:
            result = dao.get_by_name_and_phases(name, [])
        elif phases:
            result = dao.get_by_phases(phases)
        else:
            result = dao.get_by_phases(None)
        #TODO: All categories are already loaded in the database. Remove this code and update the sensor generation logic to use the database directly.
        #if runtime is not None:
        #    is_runtime = runtime.lower() in ("true", "1")
        #    result = [r for r in result if bool(r.get("runtime")) == is_runtime]

        return response_data(result, RuleCategorySchema(many=True))


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new rule category.

    Returns:
        Response: JSON response containing the created rule category or error message
    """
    try:
        with RuleCategoryDao() as dao:
            cat_dict = dao.json_load(request.json)
            pk = dao.persist(cat_dict)
            saved = dao.get_by_id(pk) or cat_dict
            return response_data(saved, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<cat_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(cat_id: str) -> Response:
    """
    Update an existing rule category.

    Args:
        cat_id: The unique identifier of the rule category to update

    Returns:
        Response: JSON response containing the updated rule category or error message
    """
    try:
        with RuleCategoryDao() as dao:
            existing = dao.get_by_id(cat_id, dependents=False)
            if not existing:
                return response_error_404()
            cat_dict = dao.json_load(request.json)
            dao.update_by_id(cat_id, cat_dict)
            updated = dao.get_by_id(cat_id) or cat_dict
            return response_data(updated, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<cat_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(cat_id: str) -> Response:
    """
    Delete a rule category.

    Args:
        cat_id: The unique identifier of the rule category to delete

    Returns:
        Response: Success message or 404 error response
    """
    with RuleCategoryDao() as dao:
        cat = dao.get_by_id(cat_id, dependents=False)
        if not cat:
            return response_error_404()
        dao.delete_by_id(cat_id)
        return response_data_removed(cat_id)
