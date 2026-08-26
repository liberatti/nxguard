import json

from flask import Blueprint, request
from marshmallow import ValidationError

from api.model.config_model import ChangeDao
from api.model.upstream_model import UpstreamDao, UpstreamStatesDao
from api.model.service_model import ServiceDao
from nxcore.controllers.base_controller import (
    response_data,
    response_error,
    response_error_404,
    response_error_parse,
    response_data_removed,
    get_pagination,
    has_any_authority,
)
from nxcore.middleware.socket_manager import emit_event

routes = Blueprint("upstream", __name__)


@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE", "PATCH"] and response.status_code in [200, 201]:
        with ChangeDao() as dao:
            if not dao.get_by_name("upstream"):
                dao.persist({"name": "upstream"})
            emit_event('tracking_evt')
    return response


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    query = request.args.get("query") or request.args.get("q") or request.args.get("name") or request.args.get("search")
    with UpstreamDao() as dao:
        result = dao.search(query=query, pagination=get_pagination())
        if result["metadata"]["total_elements"] > 0:
            for e in result['data']:
                if 'content' in e:
                    e.pop('content')
            return response_data(result, dao.pageSchema)
        else:
            return response_error_404()


@routes.route("/<upstream_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(upstream_id):
    with UpstreamDao() as dao:
        upstream = dao.get_by_id(upstream_id)
        if upstream:
            if 'content' in upstream:
                upstream.pop('content')
            return response_data(upstream, dao.schema)
        else:
            return response_error_404()


@routes.route("/<upstream_id>/states", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get_states(upstream_id):
    with UpstreamStatesDao() as dao:
        states = dao.get_states_by_upstream_id(int(upstream_id))
        return response_data(states)


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save():
    try:
        with UpstreamDao() as dao:
            if request.content_type and request.content_type.startswith('multipart/form-data'):
                metadata = request.files.get('metadata')
                raw_upstream = json.load(metadata.stream) if metadata else {}
                upstream = dao.json_load(raw_upstream)
                file = request.files.get('zipfile')
                if file:
                    upstream["content"] = file.read()
            else:
                upstream = dao.json_load(request.json)
            pk = dao.persist(upstream)
            saved = dao.get_by_id(pk) or upstream
            if 'content' in saved:
                saved.pop("content")
            return response_data(saved, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<upstream_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(upstream_id):
    try:
        with UpstreamDao() as dao, UpstreamStatesDao() as states_dao:
            if request.content_type and request.content_type.startswith('multipart/form-data'):
                metadata = request.files.get('metadata')
                raw_upstream = json.load(metadata.stream) if metadata else {}
                upstream = dao.json_load(raw_upstream)
                file = request.files.get('zipfile')
                if file:
                    upstream["content"] = file.read()
            else:
                upstream = dao.json_load(request.json)
            dao.update_by_id(upstream_id, upstream)
            states_dao.delete_by_upstream_id(int(upstream_id))
            updated = dao.get_by_id(upstream_id) or upstream
            if 'content' in updated:
                updated.pop("content")
            return response_data(updated, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<upstream_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(upstream_id):
    with UpstreamDao() as dao, ServiceDao() as service_dao:
        service_list = service_dao.get_all()
        if service_list and "data" in service_list and service_list["data"]:
            for service in service_list["data"]:
                for route in service.get("routes") or []:
                    ups = route.get("upstream")
                    ups_id = ups.get("_id") if isinstance(ups, dict) else ups
                    if ups and str(ups_id) == str(upstream_id):
                        service_name = service.get("name", "Unknown")
                        service_id = service.get("_id")
                        return response_error(
                            f"Upstream in use by service: {service_name} (ID: {service_id})",
                            code=406,
                            details={"service_id": service_id, "service_name": service_name},
                        )
        r = dao.delete_by_id(upstream_id)
        if r:
            with UpstreamStatesDao() as states_dao:
                states_dao.delete_by_upstream_id(int(upstream_id))
            return response_data_removed(upstream_id)
        else:
            return response_error_404()
