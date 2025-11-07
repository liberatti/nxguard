import csv
import gzip
import io
import os
import tarfile
import traceback
from datetime import datetime

import geoip2.database
import requests
from bson import ObjectId

from api.repository.config_model import ConfigDao
from api.repository.feed_model import FeedDao
from api.repository.geoip_model import GeoIpDao
from api.repository.rbl_model import RBLDao
from api.repository.redis_cache import RedisCache
from api.tools.network_tool import NetworkTool
from basic4web.middleware.logging import logger
from config import APP_BASE, TZ


def update():
    with ConfigDao() as dao, FeedDao() as feed_dao, RBLDao() as rbl_dao:
        conf = dao.get_active()
        download_ip2asn()
        if "maxmind_key" in conf and len(conf["maxmind_key"]) > 0:
            try:
                download_mmdb(conf["maxmind_key"], "GeoLite2-ASN")
                download_mmdb(conf["maxmind_key"], "GeoLite2-City")
            except Exception as e:
                logger.error(f"Failed to download GeoLite2: %s", e)

        for feed in feed_dao.get_by_type("network"):
            if "source" in feed and len(feed["source"]) > 1:
                try:
                    source_url = feed["source"]
                    if feed["restricted"]:
                        if "iblocklist" in feed["provider"]:
                            if (
                                    "iblocklist_username" in conf
                                    and len(conf["iblocklist_username"]) > 0
                            ):
                                source_url = f"{source_url}&username={conf['iblocklist_username']}&pin={conf['iblocklist_pin']}"
                            else:
                                logger.info(
                                    f"Feed {feed['name']} skipped, no credentials"
                                )
                                continue

                    resp = requests.get(source_url)
                    if resp and resp.status_code == 200:
                        lines = []
                        if "cdir_text" in feed["format"]:
                            lines = resp.text.splitlines()
                        if "cdir_gz" in feed["format"]:
                            with gzip.GzipFile(fileobj=io.BytesIO(resp.content)) as gz:
                                for l in gz:
                                    lines.append(l.decode("utf-8").strip())
                        rbl_dao.delete_by_provider("feed", feed["_id"])
                        fc = 0
                        for line in lines:
                            if line.strip() and "#" not in line:
                                if NetworkTool.is_network(line):
                                    rbl = dict(NetworkTool.range_from_network(line))
                                    ip_v = (
                                        4
                                        if NetworkTool.is_ipv4(line.split("/")[0])
                                        else 6
                                    )
                                    rbl.update(
                                        {
                                            "version": ip_v,
                                            "provider_type": "feed",
                                            "provider_id": ObjectId(feed["_id"]),
                                            "action": feed["action"],
                                        }
                                    )
                                    rbl_dao.persist(rbl)
                                    fc += 1

                        feed_dao.update_by_id(
                            feed["_id"], {"updated_on": datetime.now(TZ)}
                        )
                        logger.info(
                            f"Update Security IP feeds {feed['name']} with {fc} records"
                        )
                except Exception as e:
                    logger.error(f"Failed to load {feed['slug']}: %s", e)
                    logger.error(traceback.format_exc())


def download_ip2asn(feed="ip2asn-combined"):
    response = requests.get(f"https://iptoasn.com/data/{feed}.tsv.gz")
    if response.status_code == 200:
        with RedisCache() as cache:
            zip_content = io.BytesIO(response.content)
            with gzip.open(zip_content, "rt", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter="\t")
                batch = []
                for row in reader:
                    try:
                        r = {
                            "as_number": row[2],
                            "country_code": row[3],
                            "as_description": row[4],
                            "source": "ip2asn",
                            "version": 4 if NetworkTool.is_ipv4(row[0]) else 6,
                            "network": f"{row[0]}/{NetworkTool.calc_prefix_from_range(row[0], row[1])}",
                        }
                        net_start, net_end = NetworkTool.range_from_network(r["network"])
                        cache.persist(f"geoip:{net_start}:{net_end}", r)
                        batch.append(r)
                    except Exception as e:
                        logger.error(f"Failed parse {r}: %s", e)
                        logger.error(traceback.format_exc())
                dao.persist_many(batch)
                logger.info(f"Download {feed} with {len(batch)} records")


def download_mmdb(key, edition_id):
    url = f"https://download.maxmind.com/geoip_download?edition_id={edition_id}&license_key={key}&suffix=tar.gz"
    logger.info(f"{url}")
    response = requests.get(url)
    if response.status_code == 200:
        zip_content = io.BytesIO(response.content)
        with tarfile.open(fileobj=zip_content, mode="r:gz") as tar:
            os.makedirs(f"{APP_BASE}/data", exist_ok=True)
            for m in tar.getmembers():
                if m.isfile() and m.name.endswith(".mmdb"):
                    dest_path = f"{APP_BASE}/data/{edition_id}.mmdb"
                    extracted = tar.extractfile(m)
                    if extracted is not None:
                        with open(dest_path, "wb") as out_f:
                            out_f.write(extracted.read())
                    break
    else:
        logger.error(f"Failed to download {edition_id} {response}")
    logger.info(f"[update] Download {edition_id}")


def geo_info(ip):
    ip_info = {}
    model = GeoIpDao()
    ip_asn = model.find_by_ip(ip)
    if ip_asn:
        ip_info.update(
            {
                "net_start": ip_asn["net_start"],
                "net_end": ip_asn["net_end"],
                "ans_number": ip_asn["as_number"],
                "organization": ip_asn["as_description"],
                "country": ip_asn["country_code"],
            }
        )
    for db in ["ASN", "City"]:
        if os.path.exists(f"{APP_BASE}/data/GeoLite2-{db}.mmdb"):
            with geoip2.database.Reader(
                    f"{APP_BASE}/data/GeoLite2-{db}.mmdb"
            ) as reader:
                try:
                    if "ASN" in db:
                        response_asn = reader.asn(ip)
                        ip_info.update(
                            {
                                "ans_number": response_asn.autonomous_system_number,
                                "organization": response_asn.autonomous_system_organization,
                            }
                        )
                    if "City" in db:
                        response_city = reader.city(ip)
                        ip_info.update(
                            {
                                "country": response_city.country.iso_code,
                                "latitude": response_city.location.latitude,
                                "longitude": response_city.location.longitude,
                            }
                        )
                except Exception:
                    pass
    return ip_info
