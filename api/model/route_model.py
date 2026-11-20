from enum import Enum

from marshmallow import EXCLUDE, Schema, fields

from api.model.upstream_model import UpstreamSchema
from api.model.sensor_model import SensorSchema


class RouteType(str, Enum):
    UPSTREAM = "UPSTREAM"
    STATIC = "STATIC"
    REDIRECT = "REDIRECT"


class RedirectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    code = fields.Integer()
    url = fields.String()


class RouteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    service_id = fields.Integer(allow_none=True)
    name = fields.String()
    type = fields.String()
    paths = fields.List(fields.String())
    allowed_methods = fields.Raw(allow_none=True)
    allowed_content_type = fields.Raw(allow_none=True)
    upstream = fields.Nested(UpstreamSchema)
    redirect = fields.Nested(RedirectSchema)
    sensor = fields.Nested(SensorSchema)
    monitor_only = fields.Boolean()
    cache_methods = fields.List(fields.String())
