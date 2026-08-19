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
from api.model.sensor_model import SensorDao
from api.services.ipxa_services import IPXAService

routes = Blueprint("sensor", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after sensor modifications.

    Args:
        response: The Flask response object

    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [
        200,
        201,
    ]:
        with ChangeDao() as dao:
            if not dao.get_by_name("sensor"):
                dao.persist({"name": "sensor"})
            emit_event("tracking_evt")
    return response


@routes.route("/<sensor_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(sensor_id: str) -> Response:
    """
    Retrieve a specific sensor by ID.

    Args:
        sensor_id: The unique identifier of the sensor

    Returns:
        Response: JSON response containing the sensor data or 404 error
    """
    with SensorDao() as dao:
        sensor = dao.get_by_id(sensor_id)
        return (
            response_data(sensor, schema=dao.schema) if sensor else response_error_404()
        )


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new sensor.

    Returns:
        Response: JSON response containing the created sensor or error message
    """
    try:
        with SensorDao() as dao:
            sensor_dict = dao.json_load(request.json)
            pk = dao.persist(sensor_dict)
            sensor = dao.get_by_id(pk)
            return response_data(sensor, dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all sensors.

    Returns:
        Response: JSON response containing paginated sensor list or 404 error
    """
    query = (
        request.args.get("query")
        or request.args.get("q")
        or request.args.get("name")
        or request.args.get("search")
    )
    with SensorDao() as dao:
        result = dao.search(query=query, pagination=get_pagination())
        return (
            response_data(result, dao.pageSchema)
            if result["metadata"]["total_elements"] > 0
            else response_error_404()
        )


@routes.route("/<sensor_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(sensor_id: str) -> Response:
    """
    Update an existing sensor.

    Args:
        sensor_id: The unique identifier of the sensor to update

    Returns:
        Response: JSON response containing the updated sensor or error message
    """
    try:
        with SensorDao() as dao:
            sensor_dict = dao.json_load(request.json)
            result = dao.update_by_id(sensor_id, sensor_dict)
            return response_data(result, schema=dao.schema)
    except ValidationError as err:
        return response_error_parse(err)


@routes.route("/<sensor_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(sensor_id: str) -> Response:
    """
    Delete a sensor.

    Args:
        sensor_id: The unique identifier of the sensor to delete

    Returns:
        Response: Success message or error response
    """
    with SensorDao() as dao:
        result = dao.delete_by_id(sensor_id)
        return response_data_removed(sensor_id) if result else response_error_404()


@routes.route("/<sensor_id>/check/<ipaddr>", methods=["GET"])
@has_any_authority(_internal=True)
def geoip_info(ipaddr: str) -> Response:
    """
    Check GeoIP information for an IP address.

    Args:
        ipaddr: The IP address to check

    Returns:
        Response: JSON response containing GeoIP information or error response
    """
    geo = IPXAService.geo_info(ipaddr)
    ip_info = {"country": geo["country"]}
    return response_data(ip_info)
