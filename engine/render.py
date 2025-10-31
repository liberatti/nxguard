import glob
import os

from jinja2 import Environment, FileSystemLoader

from basic4web.middleware.logging import logger
from config import APP_BASE

env = Environment(loader=FileSystemLoader('engine/templates'))


def generate(data, output_dir=f"{APP_BASE}"):
    logger.info(f"[{output_dir}] - Cleanup")
    os.makedirs(f"{output_dir}/nginx/conf/", exist_ok=True)
    for file_path in glob.glob(f"{output_dir}/nginx/conf/*.conf"):
        os.remove(file_path)

    os.makedirs(f"{output_dir}/keystore/", exist_ok=True)
    for file_path in glob.glob(f"{output_dir}/keystore/*"):
        os.remove(file_path)

    logger.info(f"[{output_dir}] - Generate nginx/conf/upstream.conf")
    with open(f"{output_dir}/nginx/conf/upstream.conf", "w") as f:
        template_content = env.get_template('nginx/upstream.conf.j2').render(data)
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/monitor.conf")
    with open(f"{output_dir}/nginx/conf/monitor.conf", "w") as f:
        template_content = env.get_template('nginx/monitor.conf.j2').render(data)
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate keystore")
    for crt in data['certificates']:
        with open(f"{output_dir}/keystore/{crt['name']}.crt", "w") as f:
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

        with open(f"{output_dir}/keystore/{crt['name']}.key", "w") as f:
            template_content = env.get_template('certificate.j2').render(
                {
                    "name": crt['name'],
                    "subjects": crt['subjects'],
                    "content": crt['private_key'],
                    "not_after": crt['not_after'],
                }
            )
            f.write(template_content)

    for service in data['services']:
        logger.info(f"[{output_dir}] - Generate nginx/conf/service-{service['name']}.conf")
        for b in service['bindings']:
            if b['protocol'] == 'HTTPS':
                service.update({"ssl_enable": True})
        with open(f"{output_dir}/nginx/conf/service-{service['name']}.conf", "w") as f:
            template_content = env.get_template('nginx/service.conf.j2').render(service)
            f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/fastcgi.conf")
    with open(f"{output_dir}/nginx/conf/fastcgi.conf", "w") as f:
        template_content = env.get_template('nginx/fastcgi.conf.j2').render(data)
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/nginx.conf")
    with open(f"{output_dir}/nginx/conf/nginx.conf", "w") as f:
        template_content = env.get_template('nginx/nginx.conf.j2').render(data)
        f.write(template_content)
