import glob
import os
import re

from jinja2 import Environment, FileSystemLoader
from nxcore.middleware.logging_manager import logger

import config
from api.model.seclang_model import RuleCategoryDao
from api.model.route_model import RouteType
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(template_content)


def _generate_trusted_ips(output_dir):
    with FeedService() as ipxa_feed:
        try:
            ipsets = ipxa_feed.get_by_type("bypass")
            os.makedirs(output_dir, exist_ok=True)
            for ipset in ipsets:
                with open(f"{output_dir}/IPSET-{ipset['name']}.data", "w") as f:
                    f.write(ipset["data"])
        except Exception as e:
            logger.error(f"Error generating trusted ips: {e}")


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

    conf = data.get("config") or {}
    ipxa = conf.get("ipxa") if isinstance(conf, dict) else {}
    ipxa = ipxa or {}

    for sensor in data["sensors"]:
        sensor_name = sensor.get("render_name") or sensor.get("name")
        if isinstance(ipxa, dict) and ipxa.get("url"):
            sensor.update(
                {
                    "ipxa_enabled": True,
                    "ipxa_url": ipxa.get("url"),
                    "ipxa_key": ipxa.get("key"),
                    "blq_geo": ",".join(sensor["security"]["geo_codes"]),
                    "blq_rbl": ",".join(sensor["security"]["reputation"]),
                    "trusted": ",".join(sensor["security"]["trusted"]),
                }
            )
            # TODO create test step for lua sensor
            _render_template_to_file(
                env,
                "lua/sensor.lua",
                f"{config.LUA_LIBS_PATH}/nxguard/sensors/{sensor_name}.lua",
                sensor,
            )
        else:
            sensor["ipxa_enabled"] = False

        exclusions = sensor.get("exclusion") or sensor.get("exclusions") or []
        if isinstance(exclusions, str):
            exclusions = [x.strip() for x in exclusions.split(",") if x.strip()]
        chunk_size = 10
        exclusion_lists = [
            ",".join(
                f"ctl:ruleRemoveById={str(x).strip()}"
                for x in exclusions[i:i + chunk_size]
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
                "name": sensor_name,
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
                f"{output_dir}/modsec/coreruleset/{prefix}SENSOR-{sensor_name}.policy",
                sensor,
            )


def _normalize_name_for_render(item: dict) -> str:
    """Normalizes item name to lowercase with _id suffix if present."""
    name = str(item.get("name") or "").strip().lower()
    _id = item.get("_id")
    if _id is not None and str(_id).strip():
        _id_str = str(_id).strip()
        if not name.endswith(f"_{_id_str}"):
            name = f"{name}_{_id_str}"
    return name


def _normalize_entities(data: dict) -> None:
    """Normalizes names in services, upstreams, and sensors to lowercase with _id suffix for rendering."""
    for key in ["services", "upstreams", "sensors"]:
        if key in data and isinstance(data[key], list):
            for item in data[key]:
                if isinstance(item, dict):
                    item["render_name"] = _normalize_name_for_render(item)


def __resolve_sensor_by_name(sensor_name, data):
    if not sensor_name:
        return None
    sensors = data.get("sensors", [])
    for s in sensors:
        if isinstance(sensor_name, dict):
            ref_id = sensor_name.get("_id") or sensor_name.get("id")
            if ref_id is not None and str(s.get("_id")) == str(ref_id):
                return s
            name = sensor_name.get("name")
        else:
            name = sensor_name
            if name is not None and str(s.get("_id")) == str(name):
                return s

        if name:
            name_str = str(name).strip()
            if (
                s.get("name") == name_str
                or s.get("render_name") == name_str
                or str(s.get("name", "")).lower() == name_str.lower()
                or s.get("render_name")
                == _normalize_name_for_render({"name": name_str, "_id": s.get("_id")})
            ):
                return s
    logger.warning(
        f"__resolve_sensor_by_name: {sensor_name} not found in {data.get('sensors', [])}"
    )
    return None


def __resolve_upstream_by_name(upstream_name, data):
    if not upstream_name:
        return None
    upstreams = data.get("upstreams", [])
    for u in upstreams:
        if isinstance(upstream_name, dict):
            ref_id = upstream_name.get("_id") or upstream_name.get("id")
            if ref_id is not None and str(u.get("_id")) == str(ref_id):
                return u
            name = upstream_name.get("name")
        else:
            name = upstream_name
            if name is not None and str(u.get("_id")) == str(name):
                return u

        if name:
            name_str = str(name).strip()
            if (
                u.get("name") == name_str
                or u.get("render_name") == name_str
                or str(u.get("name", "")).lower() == name_str.lower()
                or u.get("render_name")
                == _normalize_name_for_render({"name": name_str, "_id": u.get("_id")})
            ):
                return u
    logger.warning(
        f"__resolve_upstream_by_name: {upstream_name} not found in {data.get('upstreams', [])}"
    )
    return None


def _generate_services(
    env: Environment, output_dir: str, conf_dir: str, test: bool, data: dict
) -> None:
    """Generates Nginx configuration files for each defined service."""
    logger.info(f"[{output_dir}] - Generate Services")
    prefix = "test-" if test else ""
    for service in data["services"]:
        svc_name = service.get("render_name") or service.get("name")
        service.update(
            {
                "BASE_PATH": config.BASE_PATH,
                "IS_TEST": test,
                "config": data["config"],
            }
        )
        os.makedirs(f"{output_dir}/cache/{svc_name}", exist_ok=True)
        service_path = f"{conf_dir}/service-{svc_name}.conf"
        logger.info(f"[{output_dir}] - Generate {service_path}")
        for b in service.get("bindings", []):
            if b["protocol"] == "HTTPS":
                service.update({"ssl_enable": True})

        for r in service.get("routes", []):
            if r["type"] == RouteType.UPSTREAM:
                r["upstream"] = __resolve_upstream_by_name(r.get("upstream"), data)
            if r["type"] == RouteType.STATIC:
                r.update({"upstream": None})
            if r["type"] == RouteType.REDIRECT:
                r.update({"upstream": None})

            if "sensor" in r and r.get("sensor"):
                sensor = __resolve_sensor_by_name(r["sensor"], data)
                sensor_name = (
                    (sensor.get("render_name") or sensor.get("name"))
                    if sensor
                    else (
                        r["sensor"].get("name")
                        if isinstance(r["sensor"], dict)
                        else r["sensor"]
                    )
                )
                service.update(
                    {
                        "service_policy_file": f"{output_dir}/modsec/conf/{prefix}SERVICE-{svc_name}.policy",
                    }
                )
                r.update(
                    {
                        "sensor": sensor,
                        "route_policy_file": f"{output_dir}/modsec/conf/{prefix}ROUTE-{svc_name}.{r['name']}.policy",
                        "sensor_policy_file": f"{output_dir}/modsec/coreruleset/{prefix}SENSOR-{sensor_name}.policy",
                    }
                )
                _render_template_to_file(
                    env,
                    "modsec/modsec_route.j2",
                    r["route_policy_file"],
                    r,
                )
                _render_template_to_file(
                    env,
                    "modsec/modsec_service.j2",
                    service["service_policy_file"],
                    service,
                )
        _render_template_to_file(env, "nginx/service.conf.j2", service_path, service)


def generate(data, output_dir=config.BASE_PATH, test=False):
    """Generates all Nginx configuration, sensor, and certificate files from Jinja2 templates."""
    t_dir = ["client_body", "fastcgi", "proxy", "scgi", "uwsgi"]
    for t in t_dir:
        os.makedirs(f"{output_dir}/temp/{t}", exist_ok=True)

    _normalize_entities(data)
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
        conf = data.get("config") or {}
        ipxa = conf.get("ipxa") if isinstance(conf, dict) else {}
        if isinstance(ipxa, dict) and ipxa.get("url"):
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
