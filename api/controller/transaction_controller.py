from datetime import datetime
from flask import Blueprint, request

from nxcore.controllers.base_controller import (
    response_data,
    response_error_404,
    get_pagination,
    has_any_authority
)

from nxcore.common_utils import replace_tz
from api.model.transaction_model import TransactionDao
from config import DATETIME_FMT

routes = Blueprint("trn", __name__)


@routes.route("/stats/tpm", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def st_tpm():
    req = request.json
    st_date = replace_tz(datetime.strptime(req.pop("logtime_start"), DATETIME_FMT))
    ed_date = replace_tz(datetime.strptime(req.pop("logtime_end"), DATETIME_FMT))
    with TransactionDao() as dao:
        if "filters" in req:
            tpm = dao.get_tpm(
                st_date,
                ed_date,
                req["filters"],
            )
        else:
            tpm = dao.get_tpm(
                st_date,
                ed_date,
                None,
            )
        if tpm:
            for s in tpm:
                dtj = s.pop("_id")
                dt = replace_tz(datetime(
                    dtj["year"], dtj["month"], dtj["day"], dtj["hour"], dtj["minute"]
                ))
                s.update({"logtime": dt.strftime(DATETIME_FMT)})
            return response_data(tpm)
        else:
            return response_error_404()


@routes.route("/<trn_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(trn_id):
    with TransactionDao() as dao:
        trn = dao.get_by_id(trn_id)

        if trn:
            return response_data(trn, dao.schema)
        else:
            return response_error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    with TransactionDao() as dao:
        st_date = replace_tz(datetime.strptime(
            request.json.pop("logtime_start"), DATETIME_FMT
        ))
        ed_date = replace_tz(datetime.strptime(request.json.pop("logtime_end"), DATETIME_FMT))
        _pagination = get_pagination()
        if request.json and "filters" in request.json:
            result = dao.get_all(
                _pagination,
                dt_start=st_date,
                dt_end=ed_date,
                filters=request.json["filters"],
            )
        else:
            result = dao.get_all(
                _pagination,
                dt_start=st_date,
                dt_end=ed_date,
                filters=None,
            )
        if result["metadata"]["total_elements"] > 0:
            return response_data(result, dao.pageSchema)
        else:
            return response_error_404()
