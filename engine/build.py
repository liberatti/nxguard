"""Configuration builder module for assembling, exporting, reading, and seeding database configurations."""

import json
import os

import bcrypt
from nxcore.common_utils import gen_random_string

import config
from api.model.certificate_model import CertificateDao
from api.model.config_model import ConfigDao, ConfigBackupDao, ChangeDao
from api.model.oauth_model import UserDao
from api.model.sensor_model import SensorDao
from api.model.service_model import ServiceDao
from api.model.route_model import RouteDao
from api.model.upstream_model import UpstreamDao, NodeStatusDao, UpstreamStatesDao
from api.model.transaction_model import TransactionDao
from api.tools.network_tool import NetworkTool
from nxcore.middleware.logging_manager import logger
from api.model.acme_model import ChallengeDao


def get_config():
    """Assembles active configuration from DAOs into a single dictionary."""
    c = dict()
    with ConfigDao() as dao:
        c.update({"config": dao.get_active()})

    with UpstreamDao() as dao:
        c.update({"upstreams": dao.get_all()["data"]})

    with CertificateDao() as dao:
        c.update({"certificates": dao.get_all()["data"]})

    with ServiceDao() as s_dao:
        c.update({"services": s_dao.get_all()["data"]})

    with SensorDao() as dao:
        c.update({"sensors": dao.get_all()["data"]})

    c.update(
        {
            "NGINX_DIR": os.path.join(config.BASE_PATH, "nginx"),
            "BASE_PATH": config.BASE_PATH,
        }
    )
    return c


def export_config_json(data, json_file):
    """Exports configuration dictionary as a formatted JSON file."""
    with open(os.path.join(config.DB_PATH, json_file), "w") as f:
        json.dump(data, f, indent=4)


def read_from_json(data_dir, json_file):
    """Reads and parses a JSON file from the data directory."""
    path = os.path.join(data_dir, json_file)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {path}: {e}")
    else:
        logger.warning(f"File not found: {path}")
    return None


def create_db():
    """Creates initial database schema tables and seeds default superuser."""
    with ConfigDao() as dao:
        dao.create_schema()
    with ConfigBackupDao() as dao:
        dao.create_schema()
    with UserDao() as dao:
        dao.create_schema()
        encrypted_pass = bcrypt.hashpw("admin".encode("utf8"), bcrypt.gensalt())
        user = {
            "name": "Default Admin",
            "password": encrypted_pass.decode("utf8"),
            "email": "admin@nxguard.local",
            "role": "superuser",
        }
        dao.persist(user)
    with UpstreamDao() as dao:
        dao.create_schema()
    with CertificateDao() as dao:
        dao.create_schema()
    with SensorDao() as dao:
        dao.create_schema()
    with ServiceDao() as dao:
        dao.create_schema()
    with RouteDao() as dao:
        dao.create_schema()
    with TransactionDao() as dao:
        dao.create_schema()
    with NodeStatusDao() as dao:
        dao.create_schema()
    with UpstreamStatesDao() as dao:
        dao.create_schema()
    with ChangeDao() as dao:
        dao.create_schema()
    with ChallengeDao() as dao:
        dao.create_schema()


def init_from_data(data_dir, data_file="init-data.json"):
    """Populates database tables from an initial dataset dictionary."""

    logger.info(f"Initialize from {data_dir}/{data_file}")

    data = read_from_json(data_dir, data_file)
    if not data:
        return

    if "config" in data:
        with ConfigDao() as dao:
            dao.delete_all()
            conf = data["config"]
            conf.update(
                {
                    "cluster_id": gen_random_string(8),
                    "active_scn": gen_random_string(16),
                }
            )
            if not conf.get("ca_certificate") or not conf.get("ca_private"):
                try:
                    from api.tools.ssl_tool import SSLTool

                    ca_dict = SSLTool.gen_ca("nxguard-CA")
                    conf["ca_certificate"] = SSLTool.crt_to_pem(ca_dict["certificate"])
                    conf["ca_private"] = SSLTool.private_to_pem(ca_dict["private_key"])
                except Exception as e:
                    logger.error(f"Error generating default CA during init: {e}")
            if "archive" not in conf or conf.get("archive") is None:
                conf["archive"] = {
                    "enabled": False,
                    "archive_after": 1800,
                    "type": "opensearch",
                    "url": "",
                    "username": "",
                    "password": "",
                }
            if "purge" not in conf or conf.get("purge") is None:
                conf["purge"] = {
                    "enabled": False,
                    "purge_after": 30,
                }
            dao.persist(conf)
            logger.info(f"Config: {conf['cluster_id']}")

    if "user" in data:
        with UserDao() as dao:
            dao.delete_all()
            encrypted_pass = bcrypt.hashpw(
                data["user"]["unencrypted_password"].encode("utf8"), bcrypt.gensalt()
            )
            user = {
                "name": data["user"]["name"],
                "password": encrypted_pass.decode("utf8"),
                "email": data["user"]["email"],
                "role": data["user"]["role"],
            }
            dao.persist(user)
            logger.info(f"User: {data['user']['name']}")

    if "upstreams" in data:
        with UpstreamDao() as dao:
            dao.delete_all()
            dao.persist_many(data["upstreams"])
            logger.info(f"Upstreams: {len(data['upstreams'])}")

    if "certificates" in data:
        with CertificateDao() as dao:
            dao.delete_all()
            dao.persist_many(data["certificates"])
            logger.info(f"Certificates: {len(data['certificates'])}")

    if "sensors" in data:
        with SensorDao() as dao:
            dao.delete_all()
            dao.persist_many(data["sensors"])
            logger.info(f"Sensors: {len(data['sensors'])}")

    if "services" in data:
        with ServiceDao() as dao:
            dao.delete_all()
            dao.persist_many(data["services"])
            logger.info(f"Services: {len(data['services'])}")


def validate(data):
    """Validates target hostname/IP resolution for upstreams in the configuration."""
    for u in data.get("upstreams", []):
        for t in u.get("targets", []):
            if not NetworkTool.is_host(t.get("host")):
                ipaddr = NetworkTool.hostbyname(t.get("host"))
                if ipaddr:
                    t.update({"host": ipaddr})
                else:
                    t.update({"host": "127.0.0.1", "state": "down"})
    return data
