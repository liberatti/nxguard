import glob
import os

from nxcore.middleware.logging_manager import logger
from jinja2 import Environment, FileSystemLoader

import config
from config import BASE_PATH


def clean(data, output_dir=f"{BASE_PATH}", test=False):
    logger.info(f"[{output_dir}] - Cleanup")
    files = [
        f"{output_dir}/nginx/conf/{'test-' if test else ''}mime.types",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}uwsgi_params",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}upstreams.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}monitor.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}fastcgi.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}nginx.conf",
    ]
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            logger.error(f"Error removing file {f}")

    for file_path in glob.glob(f"{output_dir}/keystore/{'test-' if test else ''}*"):
        try:
            os.remove(file_path)
        except Exception:
            logger.error(f"Error removing file {file_path}")

    for file_path in glob.glob(
        f"{output_dir}/nginx/conf/{'test-' if test else ''}service-*.conf"
    ):
        try:
            os.remove(file_path)
        except Exception:
            logger.error(f"Error removing file {file_path}")


def generate(data, output_dir=f"{BASE_PATH}", test=False):
    t_dir = ["client_body", "fastcgi", "proxy", "scgi", "uwsgi"]
    for t in t_dir:
        os.makedirs(f"{output_dir}/temp/{t}", exist_ok=True)

    data.update({"IS_TEST": test, "BASE_PATH": config.BASE_PATH})
    env = Environment(loader=FileSystemLoader("engine/templates"))

    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}mime.types", "w") as f:
        template_content = env.get_template("nginx/mime.types.j2").render(data)
        f.write(template_content)

    with open(
        f"{output_dir}/nginx/conf/{'test-' if test else ''}uwsgi_params", "w"
    ) as f:
        template_content = env.get_template("nginx/uwsgi_params.j2").render(data)
        f.write(template_content)

    logger.info(
        f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}monitor.conf"
    )
    with open(
        f"{output_dir}/nginx/conf/{'test-' if test else ''}monitor.conf", "w"
    ) as f:
        template_content = env.get_template("nginx/monitor.conf.j2").render(data)
        f.write(template_content)

    if "upstreams" in data:
        logger.info(
            f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}upstreams.conf"
        )
        with open(
            f"{output_dir}/nginx/conf/{'test-' if test else ''}upstreams.conf", "w"
        ) as f:
            template_content = env.get_template("nginx/upstreams.conf.j2").render(data)
            f.write(template_content)

    if "certificates" in data:
        os.makedirs(f"{output_dir}/keystore/", exist_ok=True)
        logger.info(f"[{output_dir}] - Generate keystore")
        for crt in data["certificates"]:
            with open(
                f"{output_dir}/keystore/{'test-' if test else ''}{crt['name']}.crt", "w"
            ) as f:
                template_content = env.get_template("certificate.j2").render(
                    {
                        "name": crt["name"],
                        "subjects": crt["subjects"],
                        "chain": crt["chain"],
                        "content": crt["certificate"],
                        "not_after": crt["not_after"],
                    }
                )
                f.write(template_content)

            with open(
                f"{output_dir}/keystore/{'test-' if test else ''}{crt['name']}.key", "w"
            ) as f:
                template_content = env.get_template("certificate.j2").render(
                    {
                        "name": crt["name"],
                        "subjects": crt["subjects"],
                        "content": crt["private_key"],
                        "not_after": crt["not_after"],
                    }
                )
                f.write(template_content)

    if "sensors" in data:
        logger.info(f"[{output_dir}] - Generate sensor")
        for sensor in data["sensors"]:
            sensor.update(
                {
                    "BASE_PATH": config.BASE_PATH,
                    "ipxa_url": data["config"]["ipxa"]["url"],
                    "ipxa_key": data["config"]["ipxa"]["key"],
                    "blq_geo": ",".join(sensor["security"]["geo_codes"]),
                    "blq_rbl": ",".join(sensor["security"]["reputation"]),
                    "trusted": ",".join(sensor["security"]["trusted"]),
                }
            )
            with open(
                f"{config.BASE_PATH}/luajit/share/lua/5.1/nxguard/sensor-{sensor['name']}.lua",
                "w",
            ) as f:
                template_content = env.get_template("sensor.lua").render(sensor)
                f.write(template_content)

    if "services" in data:
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
                f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}service-{service['name']}.conf"
            )
            if "bindings" in service:
                for b in service["bindings"]:
                    if b["protocol"] == "HTTPS":
                        service.update({"ssl_enable": True})
            with open(
                f"{output_dir}/nginx/conf/{'test-' if test else ''}service-{service['name']}.conf",
                "w",
            ) as f:
                service.update({"BASE_PATH": config.BASE_PATH})
                template_content = env.get_template("nginx/service.conf.j2").render(
                    service
                )
                f.write(template_content)

    logger.info(
        f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}fastcgi.conf"
    )
    with open(
        f"{output_dir}/nginx/conf/{'test-' if test else ''}fastcgi.conf", "w"
    ) as f:
        template_content = env.get_template("nginx/fastcgi.conf.j2").render(data)
        f.write(template_content)

    logger.info(
        f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}nginx.conf"
    )
    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}nginx.conf", "w") as f:
        template_content = env.get_template("nginx/nginx.conf.j2").render(data)
        f.write(template_content)
    # logger.info(data)
