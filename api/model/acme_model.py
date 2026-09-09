from flask_marshmallow import Schema
from marshmallow import EXCLUDE, fields


class ChallengeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    key = fields.String()
    content = fields.String()
    issued = fields.DateTime()
