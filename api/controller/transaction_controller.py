from datetime import datetime
from flask import Blueprint, request

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    get_pagination,
    has_any_authority,
)

from nxcore.common_utils import replace_tz
from api.model.transaction_model import TransactionDao
import config as env_config
from config import DATETIME_FMT

routes = Blueprint("trn", __name__)


def parse_date(date_str, fallback):
    if not date_str:
        return fallback
    for fmt in (
        DATETIME_FMT,
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return replace_tz(datetime.strptime(date_str, fmt))
        except (ValueError, TypeError):
            continue
    try:
        return replace_tz(datetime.fromisoformat(date_str))
    except Exception:
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
    with TransactionDao() as dao:
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
    with TransactionDao() as dao:
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
    with TransactionDao() as dao:
        result = dao.get_all(
            _pagination,
            dt_start=st_date,
            dt_end=ed_date,
            filters=filters,
        )
        return response_data(result, dao.pageSchema)
