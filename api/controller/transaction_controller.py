from datetime import datetime
from flask import Blueprint, request

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    get_pagination,
    has_any_authority,
)

from nxcore.common_utils import replace_tz
from api.repository.transaction_repository import TransactionDao
from api.repository.config_repository import ConfigDao
from api.services.opensearch_service import OpenSearchService
import config as env_config
from config import DATETIME_FMT, COMMON_LOG_FORMATS

routes = Blueprint("trn", __name__)


def get_transaction_storage():
    try:
        with ConfigDao() as config_dao:
            active = config_dao.get_active()
            logging_conf = active.get("logging") if active else {}
            if logging_conf and logging_conf.get("mode") == "opensearch":
                return OpenSearchService(logging_conf)
    except Exception:
        pass
    return TransactionDao()


def parse_date(date_str, fallback):
    if not date_str:
        return fallback
    # Fast path for ISO-8601 strings
    if "T" in date_str or (len(date_str) >= 10 and date_str[4] == "-" and date_str[7] == "-"):
        try:
            return replace_tz(datetime.fromisoformat(date_str.replace("Z", "+00:00")))
        except Exception:
            pass
    for fmt in COMMON_LOG_FORMATS:
        try:
            return replace_tz(datetime.strptime(date_str, fmt))
        except (ValueError, TypeError):
            continue
    return fallback



@routes.route("/stats/tpm", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def st_tpm():
    req = request.json or {}
    st_val = req.pop("logtime_start", None)
    ed_val = req.pop("logtime_end", None)
    st_date = parse_date(st_val, datetime.now(env_config.TZ))
    ed_date = parse_date(ed_val, datetime.now(env_config.TZ))

    filters = req.get("filters")
    with get_transaction_storage() as dao:
        tpm = dao.get_tpm(st_date, ed_date, filters=filters)
        if tpm:
            for s in tpm:
                dtj = s.pop("_id")
                dt = replace_tz(
                    datetime(
                        dtj["year"],
                        dtj["month"],
                        dtj["day"],
                        dtj["hour"],
                        dtj["minute"],
                    )
                )
                s.update({"logtime": dt.strftime(DATETIME_FMT)})
            return response_data(tpm)
        return response_data([])


@routes.route("/<trn_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(trn_id):
    with get_transaction_storage() as dao:
        trn = dao.get_by_id(trn_id)
        if trn:
            return response_data(trn, dao.schema)
        return response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    req = request.json or {}
    st_val = req.pop("logtime_start", None)
    ed_val = req.pop("logtime_end", None)
    st_date = parse_date(st_val, datetime.now(env_config.TZ))
    ed_date = parse_date(ed_val, datetime.now(env_config.TZ))

    filters = req.get("filters")
    _pagination = get_pagination()
    with get_transaction_storage() as dao:
        result = dao.get_all(
            _pagination,
            dt_start=st_date,
            dt_end=ed_date,
            filters=filters,
        )
        return response_data(result, dao.pageSchema)
