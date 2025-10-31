from datetime import datetime
from typing import Optional, Dict, Any

import config as config
from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO


class ChallengeDao(SQLite3DAO):
    """
    DAO for managing ACME challenges.
    
    This class extends MongoDAO to provide specific operations
    related to ACME challenges, including key management
    and cleanup of expired challenges.
    """

    def __init__(self):
        """
        Initializes the DAO with the 'challenge' collection.
        self, db_path, table_name, schema=None, conn=None
        """
        super().__init__(db_path=config.DB_PATH, table_name="challenge")

    def delete_issued_before(self, dt: datetime) -> int:
        """
        Removes challenges issued before the specified date.
        
        Args:
            dt (datetime): Cutoff date for removal
            
        Returns:
            int: Number of documents removed
            
        Raises:
            PyMongoError: If an error occurs during the delete operation
        """
        try:
            result = self.collection.delete_many({"issued": {"$lt": dt}})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error removing old challenges: {str(e)}")
            raise

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a challenge by its key.
        
        Args:
            key (str): Challenge key
            
        Returns:
            Optional[Dict[str, Any]]: Challenge document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rs = self.collection.find_one({"key": key})
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error retrieving challenge by key: {str(e)}")
            raise
