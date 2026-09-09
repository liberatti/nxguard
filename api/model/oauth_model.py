from marshmallow import EXCLUDE, Schema, fields


class OIDCToken(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(load_default="Bearer", dump_default="Bearer")
    expires_in = fields.Integer()
    provider = fields.String()


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    email = fields.String()
    password = fields.String()
    locale = fields.String(required=False)
    role = fields.String()
