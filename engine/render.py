import glob
import os

from basic4web.middleware.logging import logger
from jinja2 import Environment, FileSystemLoader

from config import APP_BASE

env = Environment(loader=FileSystemLoader('engine/templates'))


def clean(data, output_dir=f"{APP_BASE}", test=False):
    logger.info(f"[{output_dir}] - Cleanup")
    files = [
        f"{output_dir}/nginx/conf/{'test-' if test else ''}mime.types",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}uwsgi_params",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}upstreams.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}monitor.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}fastcgi.conf",
        f"{output_dir}/nginx/conf/{'test-' if test else ''}nginx.conf"
    ]
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            logger.error(f"Error removing file {f}")

    for file_path in glob.glob(f"{output_dir}/keystore/{'test-' if test else ''}*"):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing file {file_path}")

    for file_path in glob.glob(f"{output_dir}/nginx/conf/{'test-' if test else ''}service-*.conf"):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing file {file_path}")


def generate(data, output_dir=f"{APP_BASE}", test=False):
    t_dir = [
        "client_body", "fastcgi", "proxy", "scgi", "uwsgi"
    ]
    for t in t_dir:
        os.makedirs(f"{output_dir}/temp/{t}", exist_ok=True)

    data.update({"IS_TEST": test})

    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}mime.types", "w") as f:
        template_content = env.get_template('nginx/mime.types.j2').render(data)
        f.write(template_content)

    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}uwsgi_params", "w") as f:
        template_content = env.get_template('nginx/uwsgi_params.j2').render(data)
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}monitor.conf")
    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}monitor.conf", "w") as f:
        template_content = env.get_template('nginx/monitor.conf.j2').render(data)
        f.write(template_content)

    if "upstreams" in data:
        logger.info(f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}upstreams.conf")
        with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}upstreams.conf", "w") as f:
            template_content = env.get_template('nginx/upstreams.conf.j2').render(data)
            f.write(template_content)

    if "certificates" in data:
        os.makedirs(f"{output_dir}/keystore/", exist_ok=True)
        logger.info(f"[{output_dir}] - Generate keystore")
        for crt in data['certificates']:
            with open(f"{output_dir}/keystore/{'test-' if test else ''}{crt['name']}.crt", "w") as f:
                template_content = env.get_template('certificate.j2').render(
                    {
                        "name": crt['name'],
                        "subjects": crt['subjects'],
                        "chain": crt['chain'],
                        "content": crt['certificate'],
                        "not_after": crt['not_after'],
                    }
                )
                f.write(template_content)

            with open(f"{output_dir}/keystore/{'test-' if test else ''}{crt['name']}.key", "w") as f:
                template_content = env.get_template('certificate.j2').render(
                    {
                        "name": crt['name'],
                        "subjects": crt['subjects'],
                        "content": crt['private_key'],
                        "not_after": crt['not_after'],
                    }
                )
                f.write(template_content)

    if "services" in data:
        logger.info(f"[{output_dir}] - Generate Services")
        for service in data['services']:
            service.update({"APP_BASE": data['APP_BASE'], "IS_TEST": test, "config": data['config']})
            # logger.info(data['service'])
            os.makedirs(f"{output_dir}/cache/{service['name']}", exist_ok=True)
            logger.info(f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}service-{service['name']}.conf")
            for b in service['bindings']:
                if b['protocol'] == 'HTTPS':
                    service.update({"ssl_enable": True})
            with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}service-{service['name']}.conf", "w") as f:
                service.update({"APP_BASE": data['APP_BASE']})
                template_content = env.get_template('nginx/service.conf.j2').render(service)
                f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}fastcgi.conf")
    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}fastcgi.conf", "w") as f:
        template_content = env.get_template('nginx/fastcgi.conf.j2').render(data)
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/{'test-' if test else ''}nginx.conf")
    with open(f"{output_dir}/nginx/conf/{'test-' if test else ''}nginx.conf", "w") as f:
        template_content = env.get_template('nginx/nginx.conf.j2').render(data)
        f.write(template_content)
    # logger.info(data)
