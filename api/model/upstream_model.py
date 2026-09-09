from marshmallow import (
    EXCLUDE,
    Schema,
    fields,
    pre_load,
    validates_schema,
    ValidationError,
)


class UpstreamTargetSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    host = fields.String()
    port = fields.Integer()
    weight = fields.Integer()
    state = fields.String(allow_none=True)
    healthy = fields.Boolean(allow_none=True)


class UpstreamPersistSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.String(required=False)
    cookie_name = fields.String(required=False)
    cookie_domain = fields.String(required=False)
    cookie_path = fields.String(required=False)
    cookie_expire = fields.Integer(required=False)


class UpstreamSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer(required=False, allow_none=True)
    name = fields.String()
    description = fields.String()
    retry = fields.Integer()
    retry_timeout = fields.Integer()
    conn_timeout = fields.Integer()
    protocol = fields.String()  # AJP, HTTP, HTTPS
    script_path = fields.String()  # fastcgi
    type = fields.String()  # backend, static
    targets = fields.List(fields.Nested(UpstreamTargetSchema))
    persist = fields.Nested(UpstreamPersistSchema)
    index = fields.String(allow_none=True)
    content = fields.Raw(allow_none=True)
    healthy = fields.String(allow_none=True)

    @pre_load
    def process_id(self, data, **kwargs):
        if isinstance(data, dict):
            if data.get("_id") == "" or data.get("_id") is None:
                data.pop("_id", None)
        return data

    @validates_schema
    def validate_backend_targets(self, data, **kwargs):
        upstream_type = (data.get("type") or "backend").lower()
        if upstream_type == "backend":
            if data.get("_id") and "targets" not in data:
                return
            targets = data.get("targets")
            if not targets or len(targets) == 0:
                raise ValidationError(
                    "Backend upstream requires at least one target.", "targets"
                )


class NodeStatusSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    status = fields.String()
    scn = fields.String(allow_none=True)
    last_check = fields.String()
    version = fields.String()
    net_recv = fields.Float()
    net_send = fields.Float()


class UpstreamStatesSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    node_id = fields.String()
    upstream_id = fields.Integer()
    healthy = fields.String()
    last_check = fields.String()
    targets = fields.List(fields.Dict(), allow_none=True)
