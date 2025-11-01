import bcrypt
from flask import Blueprint, request
from marshmallow import ValidationError

from api.repository.oauth_model import UserDao
from basic4web.controllers.base_controller import (
    response_data,
    response_error_404,
    response_error_parse,
    get_pagination,
    has_any_authority,
    response_error_403, response_data_removed
)
from basic4web.middleware.jwt import (
    jwt_decode,
    jwt_get
)

routes = Blueprint("user", __name__)


@routes.route("/<user_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(user_id):
    with UserDao() as dao:
        user = dao.get_by_id(user_id)
        if user:
            if "password" in user:
                user.pop("password")
            return response_data(user, dao.schema)
        else:
            return response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save():
    try:
        with UserDao() as dao:
            vo = dao.json_load(request.json)
            if "password" in vo and len(vo["password"]) > 1:
                hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
                vo.update({"password": hashed.decode("utf-8")})
            dao.persist(vo)
            vo.pop("password")
            return response_data(vo, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    with UserDao() as dao:
        result = dao.get_all(pagination=get_pagination())
        if result["metadata"]["total_elements"] > 0:
            for user in result['data']:
                if "password" in user:
                    user.pop("password")
            return response_data(result, dao.pageSchema)
        else:
            return response_error_404()


@routes.route("/<user_id>/account", methods=["PUT"])
@has_any_authority(authorities=["viewer", "superuser"])
def account_update(user_id):
    try:
        with UserDao() as dao:
            jwt_token = jwt_get()
            vo = dao.json_load(request.json)
            claims = jwt_decode(jwt_token)
            if claims["sub"] == user_id:
                if "password" in vo and len(vo["password"]) > 1:
                    hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
                    vo.update({"password": hashed.decode("utf-8")})
                result = dao.update_by_id(user_id, vo)
                return response_data(result, dao.schema)
            else:
                return response_error_403("Account update failed")
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<user_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(user_id):
    try:
        with UserDao() as dao:
            vo = dao.json_load(request.json)
            if "password" in vo and len(vo["password"]) > 1:
                hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
                vo.update({"password": hashed.decode("utf-8")})
            result = dao.update_by_id(user_id, vo)
            return response_data(result, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<user_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(user_id):
    with UserDao() as dao:
        r = dao.delete_by_id(user_id)
        if r:
            return response_data_removed(user_id)
        else:
            return response_error_404()
