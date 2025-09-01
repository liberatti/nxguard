import base64
import hashlib
import json
import os
import random
import shutil
import socket
import string
import threading
import zipfile
from copy import deepcopy
from datetime import datetime
from bson import ObjectId

from api.core.middleware.logging import logger

from config import (
    TZ
)


def clear_directory(directory_path):
    if os.path.exists(directory_path):
        try:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            logger.error(e)


def unpack_zip(content, target_dir="/var/www"):
    os.mkdir(target_dir)
    zip_file_path = os.path.join(target_dir, "unpack.zip")
    with open(zip_file_path, "wb") as zip_file:
        zip_file.write(content)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    os.remove(zip_file_path)


def get_server_id():
    server_ = os.getenv("SERVERID")
    if server_ is None:
        server_ = socket.getfqdn()
    return server_

def deep_date_str(obj):
    _obj = deepcopy(obj)
    for key, value in _obj.items():
        if isinstance(value, datetime):
            _obj[key] = value.isoformat()
        elif isinstance(value, dict):
            deep_date_str(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    deep_date_str(item)
    return _obj


def deep_merge(a: dict, b: dict) -> dict:
    result = deepcopy(a)
    for bk, bv in b.items():
        av = result.get(bk)
        if isinstance(av, dict) and isinstance(bv, dict):
            result[bk] = deep_merge(av, bv)
        else:
            result[bk] = deepcopy(bv)
    return result


def hash_dict(d):
    json_str = json.dumps(d, sort_keys=True, default=json_serial)
    return hashlib.md5(json_str.encode()).hexdigest()


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"non-serializable type: {type(obj)}")

def gen_random_string(length=16):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))

def replace_tz(not_valid_before):
    if not_valid_before.tzinfo is None:
        crt_not_valid_before = not_valid_before.replace(tzinfo=TZ)
    else:
        crt_not_valid_before = not_valid_before
    return crt_not_valid_before.astimezone(TZ)

class LogCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.audit_log = []
        self.access_log = []
        self.error_log = []

