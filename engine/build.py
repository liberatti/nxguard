

from api.repository.upstream_model import UpstreamDao
from basic4web.middleware.logging import logger

def run():
    logger.info(f"Build upstreams")
    with  UpstreamDao() as ups_dao:
        for u in ups_dao.get_all()['data']:
            logger.info(u)