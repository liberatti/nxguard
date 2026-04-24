import os
import shutil
import zipfile
import pickle

from api.core.middleware.logging import logger
from api.core.repository.mongo import MongoDAO

from config import APP_BASE

class MongoTool:

    @classmethod
    def backup(cls):
        if not os.path.exists(f"{APP_BASE}/backup"):
            os.makedirs(f"{APP_BASE}/backup")
        for collection_name in ["users", "certificates","geoip","rule_cat",
                                "rules","sensors","upstreams","service","feeds"]:
            cls.data_export(collection_name)

        with zipfile.ZipFile(
            f"{APP_BASE}/backup.zip", "w", zipfile.ZIP_DEFLATED
        ) as z_ipf:
            for root, _, files in os.walk(f"{APP_BASE}/backup"):
                for file in files:
                    file_path = os.path.join(root, file)
                    z_ipf.write(
                        file_path, os.path.relpath(file_path, f"{APP_BASE}/backup")
                    )
            shutil.rmtree(f"{APP_BASE}/backup")
            return f"{APP_BASE}/backup.zip"

    @classmethod
    def restore(cls, zip_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall()
        for collection_name in ["users", "certificates","geoip","rule_cat",
                                "rules","sensors","upstreams","service","feeds"]:
            cls.data_import(collection_name)
        os.remove(zip_path)
        shutil.rmtree(f"{APP_BASE}/backup")

    def data_export(cls,collection_name, folder=f"{APP_BASE}/backup"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        dao = MongoDAO(collection_name)
        dset = list(dao.collection.find())
        logger.info(f"Export {len(dset)} to {folder}/{collection_name}.data")
        with open(f"{folder}/{collection_name}.data", "wb") as f:
            pickle.dump(dset, f)

    def data_import(cls,collection_name, folder=f"{APP_BASE}/backup"):
        with open(f"{folder}/{collection_name}.data", "rb") as f:
            dset = pickle.load(f)
            dao = MongoDAO(collection_name)
            dao.collection.delete_many({})
            if len(dset) > 0:
                logger.info(f"Import {len(dset)} to {folder}/{collection_name}.data")
                dao.collection.insert_many(dset)