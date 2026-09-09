from marshmallow import EXCLUDE, Schema, fields


class ConfigArchiveSchema(Schema):
    enabled = fields.Boolean()
    archive_after = fields.Integer()  # minutes
    purge_after = fields.Integer()  # days
    type = fields.String()  # elastic_search, opensearch, syslog
    url = fields.String()
    username = fields.String()
    password = fields.String()


class ConfigLoggingSchema(Schema):
    mode = fields.String()  # local, opensearch
    type = fields.String(allow_none=True)
    url = fields.String(allow_none=True)
    dashboard_url = fields.String(allow_none=True)
    username = fields.String(allow_none=True)
    password = fields.String(allow_none=True)


class ConfigPurgeSchema(Schema):
    enabled = fields.Boolean()
    purge_after = fields.Integer()  # days


class ConfigIpxaSchema(Schema):
    url = fields.String(allow_none=True)
    key = fields.String(allow_none=True)


class ConfigSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    cluster_id = fields.String()
    ca_certificate = fields.String(allow_none=True)
    ca_private = fields.String(allow_none=True)
    acme_directory_url = fields.String(allow_none=True)
    dns_resolver = fields.String(allow_none=True)
    active_scn = fields.String(allow_none=True)
    archive = fields.Nested(ConfigArchiveSchema, allow_none=True)
    logging = fields.Nested(ConfigLoggingSchema, allow_none=True)
    purge = fields.Nested(ConfigPurgeSchema, allow_none=True)
    ipxa = fields.Nested(ConfigIpxaSchema, allow_none=True)


class ConfigBackupSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    scn = fields.String()
    created_at = fields.DateTime()
    data = fields.Raw()


class ChangeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
