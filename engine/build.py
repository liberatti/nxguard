import json
import os

import bcrypt
from nxcore.common_utils import gen_random_string

import config
from api.model.certificate_model import CertificateDao
from api.model.config_model import ConfigDao
from api.model.oauth_model import UserDao
from api.model.sensor_model import SensorDao
from api.model.service_model import ServiceDao
from api.model.upstream_model import UpstreamDao, NodeStatusDao
from api.model.transaction_model import TransactionDao
from api.tools.network_tool import NetworkTool
from nxcore.middleware.logging_manager import logger


def get_config():
    c = dict()
    with ConfigDao() as dao:
        c.update({"config": dao.get_active()})

    with UpstreamDao() as dao:
        c.update({"upstreams": dao.get_all()["data"]})

    with CertificateDao() as dao:
        c.update({"certificates": dao.get_all()["data"]})

    with ServiceDao() as dao:
        c.update({"services": dao.get_all()["data"]})

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
    with open(os.path.join(config.DB_PATH, json_file), "w") as f:
        json.dump(data, f, indent=4)


def read_from_json(json_file, data_dir=config.DB_PATH):
    if os.path.exists(os.path.join(data_dir, json_file)):
        logger.info(f"Loading {json_file} from {data_dir}")
        with open(os.path.join(data_dir, json_file), "r") as f:
            return json.load(f)
    return None


def create_db():
    with ConfigDao() as dao:
        dao.create_schema()
    with UserDao() as dao:
        dao.create_schema()
        encrypted_pass = bcrypt.hashpw("admin".encode("utf8"), bcrypt.gensalt())
        user = {
            "name": "Default Admin",
            "password": encrypted_pass.decode("utf8"),
            "email": "admin@local",
            "role": "superuser",
        }
        dao.persist(user)
    with UpstreamDao() as dao:
        dao.create_schema()
    with CertificateDao() as dao:
        dao.create_schema()
    with ServiceDao() as dao:
        dao.create_schema()
    with SensorDao() as dao:
        dao.create_schema()
    with TransactionDao() as dao:
        dao.create_schema()
    with NodeStatusDao() as dao:
        dao.create_schema()


def init_from_data(data):
    with ConfigDao() as dao:
        dao.delete_all()
        data["config"].update({"cluster_id": gen_random_string(8)})
        dao.persist(data["config"])
        logger.info(f"Config: {data['config']['cluster_id']}")

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

    with UpstreamDao() as dao:
        dao.delete_all()
        dao.persist_many(data["upstreams"])
        logger.info(f"Upstreams: {len(data['upstreams'])}")

    with CertificateDao() as dao:
        dao.delete_all()
        dao.persist_many(data["certificates"])
        logger.info(f"Certificates: {len(data['certificates'])}")

    with ServiceDao() as dao:
        dao.delete_all()
        dao.persist_many(data["services"])
        logger.info(f"Services: {len(data['services'])}")

    with SensorDao() as dao:
        dao.delete_all()
        dao.persist_many(data["sensors"])
        logger.info(f"Sensors: {len(data['sensors'])}")


def validate(data):
    for u in data["upstreams"]:
        for t in u["targets"]:
            if not NetworkTool.is_host(t["host"]):
                ipaddr = NetworkTool.hostbyname(t["host"])
                if ipaddr:
                    t.update({"host": ipaddr})
                else:
                    t.update({"host": "127.0.0.1", "state": "down"})
    return data
