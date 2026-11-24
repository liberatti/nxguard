"""Configuration builder module for assembling, exporting, reading, and seeding database configurations."""

import json
import os

import bcrypt
from api.middleware.common_utils import gen_random_string

import config
from api.repository.certificate_repository import CertificateDao
from api.repository.config_repository import ConfigDao, ConfigBackupDao, ChangeDao
from api.repository.oauth_repository import UserDao
from api.repository.sensor_repository import SensorDao
from api.repository.service_repository import ServiceDao
from api.repository.route_repository import RouteDao
from api.repository.upstream_repository import UpstreamDao, NodeStatusDao, UpstreamStatesDao
from api.repository.transaction_repository import TransactionDao
from api.tools.network_tool import NetworkTool
from api.tools.ssl_tool import SSLTool
from api.middleware.logging_manager import logger
from api.repository.acme_repository import ChallengeDao


def get_last_applied_config():
    """Retrieves the last successfully applied configuration from ConfigBackupDao using active_scn."""
    try:
        with ConfigDao() as config_dao:
            active_scn = config_dao.get_active_scn()

        if active_scn:
            with ConfigBackupDao() as backup_dao:
                backup = backup_dao.get_by_scn(active_scn)
                if backup and "data" in backup:
                    data = backup["data"]
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception as e:
                            logger.error(f"Failed to parse active config backup JSON: {e}")
                            data = None
                    if isinstance(data, dict):
                        data.update(
                            {
                                "NGINX_DIR": os.path.join(config.BASE_PATH, "nginx"),
                                "BASE_PATH": config.BASE_PATH,
                            }
                        )
                        return data
    except Exception as e:
        logger.error(f"Error retrieving last applied configuration: {e}")
    return None


def get_config(dependents: bool = False):
    """Assembles active configuration from DAOs into a single dictionary."""
    c = dict()
    with ConfigDao() as dao:
        c.update({"config": dao.get_active()})

    with UpstreamDao() as dao:
        c.update({"upstreams": dao.get_all()["data"]})

    with CertificateDao() as dao:
        c.update({"certificates": dao.get_all()["data"]})

    with ServiceDao() as s_dao:
        c.update({"services": s_dao.get_all(dependents=dependents)["data"]})

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
        if not dao.get_active():
            dao.persist({
                "cluster_id": gen_random_string(8),
                "active_scn": None,
            })
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


def init_from_data(data_dir=None, data_file="init-data.json", data=None):
    """Populates database tables from an initial dataset dictionary or JSON file."""

    if data is None:
        if data_dir:
            logger.info(f"Initialize from {data_dir}/{data_file}")
            data = read_from_json(data_dir, data_file)
        else:
            return

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
                    ca_dict = SSLTool.gen_ca("nxguard-CA")
                    conf["ca_certificate"] = SSLTool.crt_to_pem(ca_dict["certificate"])
                    conf["ca_private"] = SSLTool.private_to_pem(ca_dict["private_key"])
                except Exception as e:
                    logger.error(f"Error generating default CA during init: {e}")
            if "logging" not in conf or conf.get("logging") is None:
                conf["logging"] = {
                    "mode": "local",
                    "type": "elasticsearch",
                    "audit_log_parts": "ABHF",
                    "url": "",
                    "username": "",
                    "password": "",
                }
            elif "audit_log_parts" not in conf["logging"]:
                conf["logging"]["audit_log_parts"] = "ABHF"
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
            cleaned_upstreams = []
            for u in data["upstreams"]:
                u_clean = dict(u)
                u_clean.pop("healthy", None)
                u_clean.pop("render_name", None)
                if isinstance(u_clean.get("persist"), dict):
                    u_clean["persist"] = dict(u_clean["persist"])
                    u_clean["persist"].pop("cookie_var", None)
                cleaned_upstreams.append(u_clean)
            dao.persist_many(cleaned_upstreams)
            logger.info(f"Upstreams: {len(cleaned_upstreams)}")

    if "certificates" in data:
        with CertificateDao() as dao:
            dao.delete_all()
            dao.persist_many(data["certificates"])
            logger.info(f"Certificates: {len(data['certificates'])}")

    if "sensors" in data:
        with SensorDao() as dao:
            dao.delete_all()
            cleaned_sensors = []
            for s in data["sensors"]:
                s_clean = dict(s)
                s_clean.pop("render_name", None)
                cleaned_sensors.append(s_clean)
            dao.persist_many(cleaned_sensors)
            logger.info(f"Sensors: {len(cleaned_sensors)}")

    if "services" in data:
        with ServiceDao() as dao:
            dao.delete_all()
            cleaned_services = []
            for s in data["services"]:
                s_clean = dict(s)
                s_clean.pop("render_name", None)
                cleaned_services.append(s_clean)
            dao.persist_many(cleaned_services)
            logger.info(f"Services: {len(cleaned_services)}")


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
