import os
import requests
from nxcore.middleware.logging import logger
from api.repository.config_model import ConfigDao


class SecurityFeedService:
    @classmethod
    def get_ipxa_config(cls):
        """Retrieve IPXA config from active database configuration or environment."""
        url = None
        key = None
        try:
            with ConfigDao() as dao:
                conf = dao.get_active()
                if conf and "ipxa" in conf:
                    ipxa_conf = conf["ipxa"]
                    url = ipxa_conf.get("url")
                    key = ipxa_conf.get("key")
        except Exception as e:
            logger.debug(f"Could not read IPXA config from database: {e}")

        # Ensure url starts with http
        if url and not url.startswith("http"):
            url = f"http://{url}"

        # Clean trailing slash
        if url:
            url = url.rstrip("/")

        return url, key

    @classmethod
    def geo_info(cls, ip: str) -> dict:
        """
        Retrieves comprehensive GeoIP, ASN, and reputation data for a specific IP address
        by calling the external IPXA service.
        """
        ip_info = {}
        url, key = cls.get_ipxa_config()
        if not url:
            logger.error("IPXA URL is not configured.")
            return ip_info

        try:
            headers = {"Content-Type": "application/json"}
            if key:
                headers["x-api-key"] = key

            api_url = f"{url}/api/ip/info/{ip}?wid=2"
            logger.debug(f"Fetching GeoIP info from IPXA: {api_url}")

            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                data = response.json()

                # Map location fields
                loc = data.get("location", {})
                country_code = loc.get("country_code")

                # Map organization/ASN fields
                org = data.get("organization", {})
                asn_number = org.get("asn_number")
                asn_name = org.get("asn_name")

                ip_info.update({
                    "country": country_code,
                    "ans_number": str(asn_number) if asn_number is not None else None,
                    "organization": asn_name,
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                })

                # Calculate network range if network info is returned
                ip_data = data.get("ip", {})
                network = ip_data.get("network")
                prefix = ip_data.get("prefix")
                if network is not None and prefix is not None:
                    from api.tools.network_tool import NetworkTool
                    try:
                        r = NetworkTool.range_from_network(f"{network}/{prefix}")
                        ip_info.update({
                            "net_start": r.get("net_start"),
                            "net_end": r.get("net_end")
                        })
                    except Exception:
                        pass
            else:
                logger.error(f"IPXA API returned error: status_code={response.status_code}, response={response.text}")
        except Exception as e:
            logger.error(f"Failed to query GeoIP from IPXA: {e}")

        return ip_info
