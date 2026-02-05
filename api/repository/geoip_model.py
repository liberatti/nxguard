from typing import Dict, Any, Optional

from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO

import config as config
from api.tools.network_tool import NetworkTool


class GeoIpDao(SQLite3DAO):
    """
    DAO for managing GeoIP data.
    
    This class extends MongoDAO to provide specific operations
    related to GeoIP lookups and IP address geolocation.
    """

    def __init__(self):
        """
        Initializes the DAO with the 'geoip' collection.
        """
        super().__init__(
            db_path=config.DB_PATH
            , table_name="geoip"
        )

    def find_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Finds GeoIP information for a given IP address.
        
        Args:
            ip (str): IP address to look up
            
        Returns:
            Optional[Dict[str, Any]]: GeoIP document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            ip_id = NetworkTool.id(ip)
            query = {"$and": [{"net_start": {"$lte": ip_id}}, {"net_end": {"$gte": ip_id}}]}
            rs = self.collection.find_one(query)
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error finding GeoIP data for IP {ip}: {str(e)}")
            raise
