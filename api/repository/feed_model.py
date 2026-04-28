from typing import Dict, Any, List, Optional

from nxcore.middleware.logging import logger
from nxcore.repository.sqlite3_base_dao import SQLite3DAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class FeedSchema(Schema):
    """
    Schema for feed validation and serialization.

    This schema defines the structure and validation rules for feed documents.
    """

    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    slug = fields.String()
    provider = fields.String()
    version = fields.String()
    type = fields.String()  # network, ruleset, network_static
    content = fields.List(fields.String())
    action = fields.String()  # pass,deny
    scope = fields.String()  # system, user
    source = fields.String()
    description = fields.String()
    update_interval = fields.String()
    updated_on = fields.DateTime(format=config.DATETIME_FMT, allow_none=True, required=False)


class FeedDao(SQLite3DAO):
    """
    DAO for managing feed data.

    This class extends MongoDAO to provide specific operations
    related to feed management, including retrieval by slug and type.
    """

    def __init__(self):
        """
        Initializes the DAO with the 'feeds' collection and schema.
        """
        super().__init__(
            db_path=config.DB_PATH,
            table_name="feeds",
            schema=FeedSchema
        )

    def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a feed by its slug.

        Args:
            slug (str): Feed slug

        Returns:
            Optional[Dict[str, Any]]: Feed document or None if not found

        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rs = self.collection.find_one({"slug": slug})
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error retrieving feed by slug: {str(e)}")
            raise

    def get_by_type(self, _type: str) -> List[Dict[str, Any]]:
        """
        Retrieves feeds by their type.

        Args:
            _type (str): Feed type to search for

        Returns:
            List[Dict[str, Any]]: List of feed documents matching the type

        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rows = list(self.collection.find({"type": {"$regex": f".*{_type}.*"}}))
            for e in rows:
                self._to_dict(e)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving feeds by type: {str(e)}")
            raise
