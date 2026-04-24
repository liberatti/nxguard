from marshmallow import EXCLUDE, Schema, fields


class DataObjectSchema(Schema):
    """
    Schema for data object validation and serialization.

    This schema defines the structure and validation rules for data objects.
    """

    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    content = fields.List(fields.String())


class SecBaseSchema(Schema):
    """
    Base schema for security language validation and serialization.

    This schema defines the common structure and validation rules
    for security language documents.
    """

    class Meta:
        unknown = EXCLUDE

    _id = fields.String(allow_none=True)
    schema_type = fields.String()
    code = fields.Integer()
    rule_order = fields.Integer(allow_none=True)
    phase = fields.Integer()
    action = fields.String()
    logging = fields.String()
    audit_log = fields.String()
    version = fields.String()

    @classmethod
    def schema_class(cls, schema_type: str) -> type:
        """
        Returns the appropriate schema class based on the schema type.

        Args:
            schema_type (str): Type of schema to return

        Returns:
            type: Schema class

        Raises:
            ValueError: If the schema type is unknown
        """
        schema_classes = {
            "SecAction": SecAction,
            "SecMarker": SecMarker,
            "SecRule": SecRule,
            "SecComponentSignature": SecComponentSignature,
        }

        if schema_type in schema_classes:
            return schema_classes[schema_type]
        else:
            raise ValueError(f"Unknown type: {schema_type}")


class SecAction(SecBaseSchema):
    """
    Schema for security action validation and serialization.

    This schema defines the structure and validation rules for security actions.
    """

    class Meta:
        unknown = EXCLUDE

    initcol = fields.List(fields.String())
    t = fields.List(fields.String())
    setvar = fields.List(fields.String())
    tag = fields.String()
    ctl = fields.List(fields.String(), allow_none=True)


class SecComponentSignature(SecBaseSchema):
    """
    Schema for component signature validation and serialization.

    This schema defines the structure and validation rules for component signatures.
    """

    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecMarker(SecBaseSchema):
    """
    Schema for security marker validation and serialization.

    This schema defines the structure and validation rules for security markers.
    """

    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecRule(SecBaseSchema):
    """
    Schema for security rule validation and serialization.

    This schema defines the structure and validation rules for security rules.
    """

    class Meta:
        unknown = EXCLUDE

    msg = fields.String(allow_none=True)
    comment = fields.String(allow_none=True)
    skip_after = fields.String(allow_none=True)
    logdata = fields.String(allow_none=True)
    severity = fields.String(allow_none=True)
    condition = fields.String(allow_none=True)
    t = fields.List(fields.String(), allow_none=True)
    ctl = fields.List(fields.String(), allow_none=True)
    scope = fields.List(fields.String(), allow_none=True)
    tags = fields.List(fields.String(), allow_none=True)
    setvar = fields.List(fields.String(), allow_none=True)
    expirevar = fields.List(fields.String(), allow_none=True)
    capture = fields.Boolean(allow_none=True)
    multi_match = fields.Boolean(allow_none=True)
    status = fields.Integer(allow_none=True)
    files = fields.List(fields.Nested(DataObjectSchema), allow_none=True)
    chain_starter = fields.Boolean(allow_none=False, load_default=False, dump_default=False)
    chain = fields.Nested("SecRule", many=True, allow_none=True)


class RuleCategorySchema(Schema):
    """
    Schema for rule category validation and serialization.

    This schema defines the structure and validation rules for rule categories.
    """

    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String(required=True)
    phase = fields.Integer(required=True)
    file = fields.String(required=False)
    rules = fields.Nested(SecBaseSchema, many=True)
    exclusions = fields.List(fields.Integer(), allow_none=True)
