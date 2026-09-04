import traceback
from datetime import datetime, timedelta
from acme import errors as ACMEerrors

import config
from nxcore.middleware.logging_manager import logger

# noinspection PyPep8Naming
from nxcore.common_utils import replace_tz
from api.model.acme_model import ChallengeDao
from api.model.certificate_model import CertificateDao
from api.model.service_model import ServiceDao
from api.model.config_model import ConfigDao
from api.tools.ssl_tool import SSLLetsEncryptTool, SSLTool


class AcmeTool:
    @classmethod
    def clean_expired_challenges(cls):
        with ChallengeDao() as dao:
            dao.delete_issued_before(
                datetime.now() + timedelta(days=config.CERTIFICATE_RENEW)
            )

    @classmethod
    def renew_self(cls, certificate):
        with ConfigDao() as dao_c:
            c = dao_c.get_active()
        if not c:
            raise ValueError("No active configuration found")
        ca = SSLTool.get_or_create_ca(c)
        with ServiceDao() as dao_s:
            services = dao_s.get_all_by_certificate_id(certificate["_id"])

        cn = None
        sans = []
        for s in services:
            if not cn:
                cn = s["sans"][0]
                sans = s["sans"][1:]
            else:
                sans.extend(s["sans"])

        self_crt = SSLTool.create_certificate(cn, sans=list(set(sans)), ca=ca)
        self_chain = []
        for c in self_crt["chain"]:
            self_chain.append(SSLTool.crt_to_pem(c))
        crt = {
            "name": certificate["name"],
            "provider": certificate["provider"],
            "chain": "\n".join(self_chain),
            "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
            "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
            "subjects": self_crt["subjects"],
            "not_before": self_crt["not_before"],
            "not_after": self_crt["not_after"],
            "force_renew": "MANAGED" == certificate["provider"],
        }
        crt.update(SSLTool.extract_info_from_crt(self_crt["certificate"]))
        with CertificateDao() as dao_crt:
            dao_crt.update_by_id(certificate["_id"], crt)

    @classmethod
    def renew_lets(cls, certificate):
        try:
            with ServiceDao() as dao_s:
                services = dao_s.get_all_by_certificate_id(certificate["_id"])
            cn = None
            sans = []
            for s in services:
                if cn:
                    sans.extend(s["sans"])
                else:
                    cn = s["sans"][0]
                    sans = s["sans"][1:]
            if cn:
                result = SSLLetsEncryptTool.create_certificate(
                    cn, sans=sans, email="fake@tooka.com.br"
                )
                if result:
                    chain_list = []
                    for c in result["chain"]:
                        c_pem = SSLTool.crt_to_pem(c)
                        chain_list.append(c_pem)
                    chain = "\n".join(chain_list)
                    certificate.update(
                        {
                            "chain": chain,
                            "certificate": SSLTool.crt_to_pem(result["certificate"]),
                            "private_key": SSLTool.private_to_pem(
                                result["private_key"]
                            ),
                            "status": "VALID",
                            "force_renew": False,
                        }
                    )
                    certificate.update(
                        SSLTool.extract_info_from_crt(result["certificate"])
                    )
                    with CertificateDao() as dao_crt:
                        dao_crt.update_by_id(certificate["_id"], certificate)
        except ACMEerrors.ValidationError as e:
            for rs in e.failed_authzrs:
                for challenge in rs.body.challenges:
                    logger.error(challenge.error)
