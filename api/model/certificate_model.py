from marshmallow import EXCLUDE, Schema, fields

import config


class CertificateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    subjects = fields.List(fields.String())
    chain = fields.String()
    certificate = fields.String()
    private_key = fields.String()
    ssl_client_ca = fields.String()
    not_before = fields.DateTime(
        format=config.DATETIME_FMT, allow_none=True, required=False
    )
    not_after = fields.DateTime(
        format=config.DATETIME_FMT, allow_none=True, required=False
    )
    status = fields.String(required=False)
    provider = fields.String(required=False)
    force_renew = fields.Boolean(required=False, load_default=False, dump_default=False)
