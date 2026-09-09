from marshmallow import EXCLUDE, Schema, fields, post_load

from api.model.certificate_model import CertificateSchema
from api.model.route_model import RouteSchema


class HeaderSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    content = fields.String()


class BindSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    port = fields.Integer()
    protocol = fields.String()
    ssl_upgrade = fields.Boolean(
        allow_none=True, load_default=False, dump_default=False
    )
    ssl_upgrade_port = fields.Integer(
        allow_none=True, load_default=443, dump_default=443
    )

    @post_load
    def make_bind(self, data, **kwargs):
        if data.get("ssl_upgrade") is None:
            data["ssl_upgrade"] = False
        if data.get("ssl_upgrade_port") is None:
            data["ssl_upgrade_port"] = 443
        return data


class ServiceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    body_limit = fields.Integer()
    timeout = fields.Integer()
    active = fields.Boolean()
    buffer = fields.Integer()
    bindings = fields.Nested(BindSchema, many=True)
    headers = fields.Nested(HeaderSchema, many=True)
    routes = fields.Nested(RouteSchema, many=True, allow_none=True)
    compression_types = fields.List(fields.String())
    rate_limit_per_sec = fields.Integer()
    sans = fields.List(fields.String())
    ssl_protocols = fields.List(fields.String())
    certificate = fields.Nested(CertificateSchema)
    ssl_client_ca = fields.String()
    ssl_client_auth = fields.Boolean()
