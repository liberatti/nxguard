import json

import bcrypt

from api.repository.certificate_model import CertificateDao
from api.repository.config_model import ConfigDao
from api.repository.oauth_model import UserDao
from api.repository.upstream_model import UpstreamDao
from api.tools.network_tool import NetworkTool
from basic4web.common_utils import gen_random_string


def export_config_json(data, json_file):
    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)


def init_from_json(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

        with ConfigDao() as dao:
            dao.create_schema()
            data['config'].update({"cluster_id": gen_random_string(8)})
            dao.persist(data['config'])

        with UserDao() as dao:
            dao.create_schema()
            encrypted_pass = bcrypt.hashpw(data['user']['password'].encode("utf8"), bcrypt.gensalt())
            user = {
                "name": data['user']['name'],
                "password": encrypted_pass.decode("utf8"),
                "email": data['user']['email'],
                "role": data['user']['role']
            }
            dao.persist(user)

        with UpstreamDao() as dao:
            dao.create_schema()
            dao.persist_many(data['upstreams'])

        with CertificateDao() as dao:
            dao.create_schema()
            dao.persist_many(data['certificates'])

        return data


def validate(data):
    for u in data['upstreams']:
        for t in u['targets']:
            if not NetworkTool.is_host(t['host']):
                ipaddr = NetworkTool.hostbyname(t['host'])
                if ipaddr:
                    t.update({"host": ipaddr})
                else:
                    t.update({"host": '127.0.0.1', "state": 'down'})
    return data
