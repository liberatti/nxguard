from marshmallow import EXCLUDE, Schema, fields


class TransactionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Raw(required=False)
    logtime = fields.Raw(required=False)
    unique_id = fields.String(required=False)
    server_id = fields.String(required=False)
    service = fields.Dict(required=False)
    action = fields.String(required=False)
    limit_req_status = fields.String(required=False)
    geoip_status = fields.String(required=False)
    rbl_status = fields.String(required=False)
    ipxa = fields.String(required=False)
    rate_limit = fields.Dict(required=False)
    geoip = fields.Dict(required=False)
    reputation = fields.Dict(required=False)
    mtls = fields.Dict(required=False)
    user_agent = fields.Dict(required=False)
    source = fields.Dict(required=False)
    destination = fields.Dict(required=False)
    http = fields.Dict(required=False)
    route_name = fields.String(required=False)
    sensor = fields.Dict(required=False)
    upstream = fields.Dict(required=False)
    audit = fields.Dict(required=False)
    score = fields.Integer(required=False, allow_none=True)
    archived = fields.Boolean(required=False, allow_none=True)
