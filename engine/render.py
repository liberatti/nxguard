import glob
import os
import re

from jinja2 import Environment, FileSystemLoader
from nxcore.middleware.logging_manager import logger

from engine.seclang.seclang_indexer import get_default_vars
import config
from api.model.seclang_model import RuleCategoryDao
from api.services.ipxa_services import FeedService


def _remove_file(file_path: str) -> None:
    """Removes a file safely if it exists, logging an error on failure."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        logger.error(f"Error removing file {file_path}")


def _render_template_to_file(
    env: Environment, template_name: str, output_path: str, context: dict
) -> None:
    """Renders a Jinja2 template with the given context and writes it to output_path."""
    template_content = env.get_template(template_name).render(context)
    # Collapse multiple consecutive blank lines into a single blank line while preserving indentation
    template_content = re.sub(r"\n[ \t]*\n([ \t]*\n)+", "\n\n", template_content)
    with open(output_path, "w") as f:
        f.write(template_content)


def _generate_trusted_ips(output_dir):
    with FeedService() as ipxa_feed:
        ipsets = ipxa_feed.get_by_type("bypass")
        for ipset in ipsets:
            with open(f"{output_dir}/IPSET-{ipset['name']}.data", "w") as f:
                f.write(ipset["data"])


def clean(data, output_dir=config.BASE_PATH, test=False):
    """Removes generated Nginx configurations, certificates, and service files."""
    conf_dir = f"{output_dir}/nginx/conf/tests" if test else f"{output_dir}/nginx/conf"
    logger.info(f"[{output_dir}] - Cleanup (test={test})")
    if test:
        for pattern in [
            f"{output_dir}/keystore/test-*",
            f"{conf_dir}/*",
        ]:
            for file_path in glob.glob(pattern):
                _remove_file(file_path)
    else:
        files = [
            f"{conf_dir}/mime.types",
            f"{conf_dir}/uwsgi_params",
            f"{conf_dir}/fastcgi_params",
            f"{conf_dir}/scgi_params",
            f"{conf_dir}/upstreams.conf",
            f"{conf_dir}/monitor.conf",
            f"{conf_dir}/fastcgi.conf",
            f"{conf_dir}/nginx.conf",
        ]
        for f in files:
            _remove_file(f)

        for pattern in [
            f"{output_dir}/keystore/*",
            f"{conf_dir}/service-*.conf",
        ]:
            for file_path in glob.glob(pattern):
                if not os.path.basename(file_path).startswith("test-"):
                    _remove_file(file_path)


def _generate_certificates(
    env: Environment, output_dir: str, prefix: str, certificates: list
) -> None:
    """Generates certificate (.crt) and private key (.key) files in the keystore directory."""
    os.makedirs(f"{output_dir}/keystore/", exist_ok=True)
    logger.info(f"[{output_dir}] - Generate keystore")
    for crt in certificates:
        _render_template_to_file(
            env,
            "certificate.j2",
            f"{output_dir}/keystore/{prefix}{crt['name']}.crt",
            {
                "name": crt["name"],
                "subjects": crt["subjects"],
                "chain": crt["chain"],
                "content": crt["certificate"],
                "not_after": crt["not_after"],
            },
        )

        _render_template_to_file(
            env,
            "certificate.j2",
            f"{output_dir}/keystore/{prefix}{crt['name']}.key",
            {
                "name": crt["name"],
                "subjects": crt["subjects"],
                "content": crt["private_key"],
                "not_after": crt["not_after"],
            },
        )


def _generate_sensors(
    env: Environment, output_dir: str, data: dict, test: bool
) -> None:
    """Generates Lua sensor configuration files for LuaJIT."""
    logger.info(f"[{output_dir}] - Generate sensor")
    prefix = "test-" if test else ""

    for sensor in data["sensors"]:
        sensor.update(
            {
                "ipxa_url": data["config"]["ipxa"]["url"],
                "ipxa_key": data["config"]["ipxa"]["key"],
                "blq_geo": ",".join(sensor["security"]["geo_codes"]),
                "blq_rbl": ",".join(sensor["security"]["reputation"]),
                "trusted": ",".join(sensor["security"]["trusted"]),
            }
        )

        exclusions = sensor.get("exclusion") or sensor.get("exclusions") or []
        if isinstance(exclusions, str):
            exclusions = [x.strip() for x in exclusions.split(",") if x.strip()]
        chunk_size = 10
        exclusion_lists = [
            ",".join(
                f"ctl:ruleRemoveById={str(x).strip()}"
                for x in exclusions[i : i + chunk_size]
            )
            for i in range(0, len(exclusions), chunk_size)
        ]
        trusted_ipsets = []
        for t in sensor["security"]["trusted"]:
            if os.path.exists(f"{output_dir}/modsec/coreruleset/IPSET-{t}.data"):
                trusted_ipsets.append(t)
            else:
                logger.warning(
                    f"Trusted ipset {t} not found for sensor {sensor['name']}"
                )

        sensor.update(
            {
                "name": sensor["name"].lower(),
                "inbound_anomaly_score_threshold": sensor["inspection"]["score"][
                    "inbound"
                ],
                "outbound_anomaly_score_threshold": sensor["inspection"]["score"][
                    "outbound"
                ],
                "paranoia_level": sensor["inspection"]["level"],
                "exclusion_lists": exclusion_lists,
                "trusted_ipsets": trusted_ipsets,
            }
        )
        os.makedirs(f"{config.LUA_LIBS_PATH}/nxguard/sensors", exist_ok=True)

        # TODO create test step for lua sensor
        _render_template_to_file(
            env,
            "lua/sensor.lua",
            f"{config.LUA_LIBS_PATH}/nxguard/sensors/{sensor['name']}.lua",
            sensor,
        )

        with RuleCategoryDao() as dao:
            ordered_cats = dao.get_all(order_by="seq")
            categories = []

            sensor_cats = {
                cat if isinstance(cat, str) else (cat.get("name") or cat.get("_id"))
                for cat in sensor.get("categories", [])
            }
            for c in ordered_cats["data"]:
                if bool(c.get("system")) or c.get("name") in sensor_cats:
                    if c.get("file"):
                        file_path = f"{output_dir}/modsec/coreruleset/{c['file']}"
                        if os.path.exists(file_path):
                            with open(file_path, "r", encoding="utf-8") as r_data:
                                c.update({"rules": r_data.read()})
                    categories.append(c)

            sensor.update({"categories": categories})
            _render_template_to_file(
                env,
                "modsec/modsec_sensor.j2",
                f"{output_dir}/modsec/coreruleset/{prefix}sensor-{sensor['name']}.policy",
                sensor,
            )


def __resolve_sensor(sensor_ref, data):
    sensors = data.get("sensors", [])
    if isinstance(sensor_ref, dict):
        if "name" in sensor_ref and sensor_ref["name"]:
            target_name = str(sensor_ref["name"]).lower()
            for s in sensors:
                if s.get("name", "").lower() == target_name:
                    return s
        if "_id" in sensor_ref and sensor_ref["_id"] is not None:
            target_id = str(sensor_ref["_id"])
            for s in sensors:
                if str(s.get("_id")) == target_id:
                    return s
        if sensor_ref.get("name"):
            return sensor_ref

    elif sensor_ref is not None and sensor_ref != "":
        target = str(sensor_ref).lower()
        for s in sensors:
            if s.get("name", "").lower() == target or str(s.get("_id")) == target:
                return s

    if sensors:
        return sensors[0]

    return None


def __resolve_upstream(upstream_ref, data):
    upstreams = data.get("upstreams", [])
    if isinstance(upstream_ref, dict):
        if "name" in upstream_ref and upstream_ref["name"]:
            target_name = str(upstream_ref["name"])
            for u in upstreams:
                if u.get("name") == target_name:
                    return u
            return upstream_ref
        if "_id" in upstream_ref and upstream_ref["_id"] is not None:
            target_id = str(upstream_ref["_id"])
            for u in upstreams:
                if str(u.get("_id")) == target_id:
                    return u
        if upstreams:
            return upstreams[0]
        return upstream_ref

    if upstream_ref is not None and upstream_ref != "":
        target = str(upstream_ref)
        for u in upstreams:
            if u.get("name") == target or str(u.get("_id")) == target:
                return u
        if upstreams:
            return upstreams[0]
        return {"name": target}

    if upstreams:
        return upstreams[0]

    return {"name": ""}


def _generate_services(
    env: Environment, output_dir: str, conf_dir: str, test: bool, data: dict
) -> None:
    """Generates Nginx configuration files for each defined service."""
    logger.info(f"[{output_dir}] - Generate Services")
    prefix = "test-" if test else ""
    for service in data["services"]:
        service.update(
            {
                "BASE_PATH": config.BASE_PATH,
                "IS_TEST": test,
                "config": data["config"],
            }
        )
        os.makedirs(f"{output_dir}/cache/{service['name']}", exist_ok=True)
        service_path = f"{conf_dir}/service-{service['name']}.conf"
        logger.info(f"[{output_dir}] - Generate {service_path}")
        if "bindings" in service:
            for b in service["bindings"]:
                if b["protocol"] == "HTTPS":
                    service.update({"ssl_enable": True})

        if "routes" in service:
            for r in service["routes"]:
                r["upstream"] = __resolve_upstream(r.get("upstream"), data)
                sensor = __resolve_sensor(r.get("sensor"), data)

                if sensor and sensor.get("name"):
                    s_name = sensor["name"].lower()

                    service.update(
                        {
                            "has_inspection": True,
                            "service_policy_file": f"{output_dir}/modsec/conf/{prefix}service-{service['name']}.policy",
                        }
                    )
                    if "allowed_methods" not in r or r["allowed_methods"] is None:
                        r["allowed_methods"] = [
                            "GET",
                            "HEAD",
                            "POST",
                            "OPTIONS",
                            "PUT",
                            "PATCH",
                            "DELETE",
                        ]
                    if (
                        "allowed_content_type" not in r
                        or r["allowed_content_type"] is None
                    ):
                        r["allowed_content_type"] = [
                            "application/x-www-form-urlencoded",
                            "multipart/form-data",
                            "text/xml",
                            "application/xml",
                            "application/soap+xml",
                            "application/json",
                        ]
                    r.update(
                        {
                            "sensor": sensor,
                            "route_policy_file": f"{output_dir}/modsec/conf/{prefix}route-{service['name']}.{r['name']}.policy",
                            "sensor_policy_file": f"{output_dir}/modsec/coreruleset/{prefix}sensor-{s_name}.policy",
                        }
                    )
                    _render_template_to_file(
                        env,
                        "modsec/modsec_route.j2",
                        r["route_policy_file"],
                        r,
                    )
                elif sensor:
                    r["sensor"] = sensor

        _render_template_to_file(env, "nginx/service.conf.j2", service_path, service)

        if "has_inspection" in service:
            _render_template_to_file(
                env,
                "modsec/modsec_service.j2",
                service["service_policy_file"],
                service,
            )


def generate(data, output_dir=config.BASE_PATH, test=False):
    """Generates all Nginx configuration, sensor, and certificate files from Jinja2 templates."""
    t_dir = ["client_body", "fastcgi", "proxy", "scgi", "uwsgi"]
    for t in t_dir:
        os.makedirs(f"{output_dir}/temp/{t}", exist_ok=True)

    data.update({"IS_TEST": test, "config.BASE_PATH": config.BASE_PATH})
    env = Environment(loader=FileSystemLoader("engine/templates"))

    conf_dir = (
        f"{output_dir}/nginx/conf/tests" if test else f"{output_dir}/nginx/conf/enabled"
    )
    os.makedirs(conf_dir, exist_ok=True)

    _render_template_to_file(
        env,
        "nginx/mime.types.j2",
        f"{conf_dir}/mime.types",
        data,
    )
    _render_template_to_file(
        env,
        "nginx/uwsgi_params.j2",
        f"{conf_dir}/uwsgi_params",
        data,
    )
    _render_template_to_file(
        env,
        "nginx/fastcgi_params.j2",
        f"{conf_dir}/fastcgi_params",
        data,
    )
    _render_template_to_file(
        env,
        "nginx/scgi_params.j2",
        f"{conf_dir}/scgi_params",
        data,
    )

    logger.info(f"[{output_dir}] - Generate {conf_dir}/monitor.conf")
    _render_template_to_file(
        env,
        "nginx/monitor.conf.j2",
        f"{conf_dir}/monitor.conf",
        data,
    )

    if "upstreams" in data:
        logger.info(f"[{output_dir}] - Generate {conf_dir}/upstreams.conf")
        _render_template_to_file(
            env,
            "nginx/upstreams.conf.j2",
            f"{conf_dir}/upstreams.conf",
            data,
        )

    if "certificates" in data:
        prefix = "test-" if test else ""
        _generate_certificates(env, output_dir, prefix, data["certificates"])

    if "sensors" in data:
        _generate_trusted_ips(f"{config.BASE_PATH}/modsec/coreruleset")
        _generate_sensors(env, output_dir, data, test)

    if "services" in data:
        _generate_services(env, output_dir, conf_dir, test, data)

    logger.info(f"[{output_dir}] - Generate {conf_dir}/fastcgi.conf")
    _render_template_to_file(
        env,
        "nginx/fastcgi.conf.j2",
        f"{conf_dir}/fastcgi.conf",
        data,
    )

    logger.info(f"[{output_dir}] - Generate {conf_dir}/nginx.conf")
    _render_template_to_file(env, "nginx/nginx.conf.j2", f"{conf_dir}/nginx.conf", data)
