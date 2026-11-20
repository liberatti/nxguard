from marshmallow import EXCLUDE, Schema, fields


class SensorSecuritySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    geo_codes = fields.List(fields.String(), allow_none=True)
    reputation = fields.List(fields.String(), allow_none=True)
    trusted = fields.List(fields.String(), allow_none=True)


class SensorScoreSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    inbound = fields.Integer(allow_none=True)
    outbound = fields.Integer(allow_none=True)


class SensorVariablesSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    allowed_http_versions = fields.Raw(allow_none=True)
    max_file_size = fields.Integer(allow_none=True)
    restricted_extensions = fields.Raw(allow_none=True)
    max_num_args = fields.Integer(allow_none=True)
    arg_name_length = fields.Integer(allow_none=True)
    arg_length = fields.Integer(allow_none=True)


class SensorInspectionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    score = fields.Nested(SensorScoreSchema, allow_none=True)
    level = fields.Integer(allow_none=True)
    variables = fields.Nested(SensorVariablesSchema, allow_none=True)


class SensorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True)
    categories = fields.List(fields.String(), allow_none=True)
    exclusions = fields.List(fields.Raw(), allow_none=True)
    security = fields.Nested(SensorSecuritySchema, allow_none=True)
    inspection = fields.Nested(SensorInspectionSchema, allow_none=True)
