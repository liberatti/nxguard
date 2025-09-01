from functools import wraps
import jwt
from flask import jsonify, request
from flask import Response, jsonify
import config   
from api.core.middleware.jwt import jwt_get,jwt_decode
import traceback

def get_pagination():
    _pagination = None
    if "size" in request.args and "page" in request.args:
        _pagination = {
            "per_page": int(request.args.get("size")),
            "page": int(request.args.get("page")),
        }
    return _pagination

def has_any_authority(authorities=None,_internal=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not config.SECURITY_ENABLED:
                return fn(*args, **kwargs)
     
            try:
                token = jwt_get()
                if token:
                    payload = jwt_decode(token)
                    if any(a in payload.get("authorities", []) for a in authorities):
                        return fn(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return response_error_401(
                    msg="Expired authorization", details=traceback.format_exc()
                )
            except Exception as e2:
                return response_error_401(
                    msg=str(e2), details=traceback.format_exc()
                )
            return response_error_403(message="Invalid authorization")

        return decorator

    return wrapper

def response_error_404():
        return (
            jsonify(
                {
                    "message": "No results found. Check url again",
                    "code": 404,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            200,
        )

def response_error( msg="Bad Request", details="", code=400):
        return (
            jsonify(
                {
                    "message": msg,
                    "code": code,
                    "details": details,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            code,
        )

def response_error_401( msg="Not authenticated", details=""):
        return (
            jsonify(
                {
                    "message": msg,
                    "code": 401,
                    "details": details,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            401,
        )

def response_error_403( message="Not authorized"):
        return (
            jsonify(
                {
                    "message": message,
                    "code": 403,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            403,
        )

def response_error_500( msg, code=500, details=""):
        return (
            jsonify(
                {
                    "message": msg,
                    "details": details,
                    "code": code,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            500,
        )

def response_data_removed( desc):
        return (
            jsonify({"message": f"Record {desc} removed", "code": 200}),
            200,
        )

def response_ok( desc):
        return (
            jsonify({"message": desc, "code": 200}),
            200,
        )

def response_error_parse( err):
        return (
            jsonify(
                {
                    "message": "Validation Error",
                    "details": err.messages,
                    "code": 400,
                    "url": request.url,
                    "method": request.method,
                    # "valid_data": err.valid_data,
                }
            ),
            400,
        )

def response_data_list( o, schema=None):
        if schema:
            return jsonify(schema.dump(o)), 200
        else:
            return jsonify(o), 200

def response_data( o, schema=None):
        if schema:
            return jsonify(schema.dump(o)), 200
        else:
            return jsonify(o), 200

def response_redirect( url, status_code=302):
        """
        Redirect to a specific URL
        :param url: The URL to redirect to
        :param status_code: HTTP status code (default: 302 - Found)
        :return: Response object with redirect
        """
        return Response(
            response=None,
            status=status_code,
            headers={'Location': url}
        )
