from flask import Blueprint, request, Response

from nxcore.controllers.base_controller import (
    response_error_404,
    has_any_authority,
    response_data,
)


from api.model.seclang_model import RuleCategoryDao
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
            result = dao.get_by_phases([])
        return response_data(result, RuleCategorySchema(many=True))
