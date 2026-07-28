import glob
import os

from jinja2 import Environment, FileSystemLoader
from nxcore.middleware.logging_manager import logger

import config
from config import BASE_PATH


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
    with open(output_path, "w") as f:
        f.write(template_content)


def clean(data, output_dir=BASE_PATH, test=False):
    """Removes generated Nginx configurations, certificates, and service files."""
    logger.info(f"[{output_dir}] - Cleanup (test={test})")
    if test:
        for pattern in [
            f"{output_dir}/keystore/test-*",
            f"{output_dir}/nginx/conf/test-*",
        ]:
            for file_path in glob.glob(pattern):
                _remove_file(file_path)
    else:
        files = [
            f"{output_dir}/nginx/conf/mime.types",
            f"{output_dir}/nginx/conf/uwsgi_params",
            f"{output_dir}/nginx/conf/upstreams.conf",
            f"{output_dir}/nginx/conf/monitor.conf",
            f"{output_dir}/nginx/conf/fastcgi.conf",
            f"{output_dir}/nginx/conf/nginx.conf",
        ]
        for f in files:
            _remove_file(f)

        for pattern in [
            f"{output_dir}/keystore/*",
            f"{output_dir}/nginx/conf/service-*.conf",
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


def _generate_sensors(env: Environment, output_dir: str, data: dict) -> None:
    """Generates Lua sensor configuration files for LuaJIT."""
    logger.info(f"[{output_dir}] - Generate sensor")
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
        sensor.update({"name": sensor["name"].lower()})
        os.makedirs(f"{config.LUA_LIBS_PATH}/nxguard/sensors", exist_ok=True)
        _render_template_to_file(
            env,
            "sensor.lua",
            f"{config.LUA_LIBS_PATH}/nxguard/sensors/{sensor['name']}.lua",
            sensor,
        )


def _generate_services(
    env: Environment, output_dir: str, prefix: str, test: bool, data: dict
) -> None:
    """Generates Nginx configuration files for each defined service."""
    logger.info(f"[{output_dir}] - Generate Services")
    for service in data["services"]:
        service.update(
            {
                "BASE_PATH": config.BASE_PATH,
                "IS_TEST": test,
                "config": data["config"],
            }
        )
        os.makedirs(f"{output_dir}/cache/{service['name']}", exist_ok=True)
        logger.info(
            f"[{output_dir}] - Generate nginx/conf/{prefix}service-{service['name']}.conf"
        )
        if "bindings" in service:
            for b in service["bindings"]:
                if b["protocol"] == "HTTPS":
                    service.update({"ssl_enable": True})

        service_path = f"{output_dir}/nginx/conf/{prefix}service-{service['name']}.conf"
        _render_template_to_file(env, "nginx/service.conf.j2", service_path, service)


def generate(data, output_dir=BASE_PATH, test=False):
    """Generates all Nginx configuration, sensor, and certificate files from Jinja2 templates."""
    t_dir = ["client_body", "fastcgi", "proxy", "scgi", "uwsgi"]
    for t in t_dir:
        os.makedirs(f"{output_dir}/temp/{t}", exist_ok=True)

    data.update({"IS_TEST": test, "BASE_PATH": config.BASE_PATH})
    env = Environment(loader=FileSystemLoader("engine/templates"))
    prefix = "test-" if test else ""

    _render_template_to_file(
        env, "nginx/mime.types.j2", f"{output_dir}/nginx/conf/{prefix}mime.types", data
    )
    _render_template_to_file(
        env,
        "nginx/uwsgi_params.j2",
        f"{output_dir}/nginx/conf/{prefix}uwsgi_params",
        data,
    )

    logger.info(f"[{output_dir}] - Generate nginx/conf/{prefix}monitor.conf")
    _render_template_to_file(
        env,
        "nginx/monitor.conf.j2",
        f"{output_dir}/nginx/conf/{prefix}monitor.conf",
        data,
    )

    if "upstreams" in data:
        logger.info(f"[{output_dir}] - Generate nginx/conf/{prefix}upstreams.conf")
        _render_template_to_file(
            env,
            "nginx/upstreams.conf.j2",
            f"{output_dir}/nginx/conf/{prefix}upstreams.conf",
            data,
        )

    if "certificates" in data:
        _generate_certificates(env, output_dir, prefix, data["certificates"])

    if "sensors" in data:
        _generate_sensors(env, output_dir, data)

    if "services" in data:
        _generate_services(env, output_dir, prefix, test, data)

    logger.info(f"[{output_dir}] - Generate nginx/conf/{prefix}fastcgi.conf")
    _render_template_to_file(
        env,
        "nginx/fastcgi.conf.j2",
        f"{output_dir}/nginx/conf/{prefix}fastcgi.conf",
        data,
    )

    logger.info(f"[{output_dir}] - Generate nginx/conf/{prefix}nginx.conf")
    _render_template_to_file(
        env, "nginx/nginx.conf.j2", f"{output_dir}/nginx/conf/{prefix}nginx.conf", data
    )
