import glob
import os

from jinja2 import Environment, FileSystemLoader

from basic4web.middleware.logging import logger
from config import APP_BASE

env = Environment(loader=FileSystemLoader('engine/templates'))


def generate(data, output_dir=f"{APP_BASE}"):
    os.makedirs(f"{output_dir}/nginx/conf/", exist_ok=True)

    logger.info(f"[{output_dir}] - Remove nginx/conf/*.conf")
    for file_path in glob.glob(f"{output_dir}/nginx/conf/*.conf"):
        os.remove(file_path)

    logger.info(f"[{output_dir}] - Generate nginx/conf/upstream.conf")
    template_content = env.get_template('nginx/upstream.conf.j2').render(data)
    with open(f"{output_dir}/nginx/conf/upstream.conf", "w") as f:
        f.write(template_content)
    logger.info(f"[{output_dir}] - Generate nginx/conf/monitor.conf")
    template_content = env.get_template('nginx/monitor.conf.j2').render(data)
    with open(f"{output_dir}/nginx/conf/monitor.conf", "w") as f:
        f.write(template_content)

    for service in data['services']:
        logger.info(f"[{output_dir}] - Generate nginx/conf/service-{service['name']}.conf")
        template_content = env.get_template('nginx/monitor.conf.j2').render(service)
        with open(f"{output_dir}/nginx/conf/service-{service['name']}.conf", "w") as f:
            f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/fastcgi.conf")
    template_content = env.get_template('nginx/fastcgi.conf.j2').render(data)
    with open(f"{output_dir}/nginx/conf/fastcgi.conf", "w") as f:
        f.write(template_content)

    logger.info(f"[{output_dir}] - Generate nginx/conf/nginx.conf")
    template_content = env.get_template('nginx/nginx.conf.j2').render(data)
    with open(f"{output_dir}/nginx/conf/nginx.conf", "w") as f:
        f.write(template_content)
