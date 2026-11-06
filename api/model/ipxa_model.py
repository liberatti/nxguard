from marshmallow import EXCLUDE, Schema, fields
import config


class FeedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    slug = fields.String()
    provider = fields.String()
    version = fields.String()
    type = fields.String()
    content = fields.List(fields.String())
    action = fields.String()
    scope = fields.String()
    source = fields.String()
    description = fields.String()
    update_interval = fields.String()
    updated_on = fields.DateTime(
        format=config.DATETIME_FMT, allow_none=True, required=False
    )
