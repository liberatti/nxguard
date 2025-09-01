import os
import threading
import time
import traceback
import schedule
from flask import Flask, Blueprint
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_restful import Api

from api.core.middleware.logging import logger
from api.core.middleware.socket_manager import init_socketio
from api.core.controllers.base_controller import response_error_404, response_error_500

from api.common_utils import  gen_random_string
from api.model.config_model import ConfigDao
from api.tools.archive_tool import LogArchiverTool
from api.tools.cluster_tool import ClusterTool
from api.tools.feed_tool import  JailTool
from cli import install
import config as env_config
from api.routes import register as register_api_routes

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limite de 16MB

cors = CORS(resources={r"/*": {"origins": "*"}})
#cors = CORS(resources=env_config.CORS)
cors.init_app(app)

ma = Marshmallow()
ma.init_app(app)

socketio = init_socketio(app)

api = Api(app)

bp = Blueprint("gw", __name__, template_folder="templates")
register_api_routes(app,bp)
app.register_blueprint(bp)

@app.errorhandler(404)
def not_found_error(error):
    return response_error_404()

@app.errorhandler(500)
def internal_error(error):
    stack_trace = traceback.format_exc()
    logger.error(f"500 Error: {error}, Stack Trace: {stack_trace}")
    return response_error_500("Unexpected Server Error", details=stack_trace)

@app.errorhandler(Exception)
def handle_exception(error):
        stack_trace = traceback.format_exc()
        logger.error(f"Internal Server Error: {stack_trace}")
        return response_error_500("Unexpected Server Error", details=stack_trace)

def _scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as ex:
            app.logger.error(f"Error running scheduled task: {ex}")
        time.sleep(1)

with app.app_context():
    if not os.path.exists(f"{env_config.APP_BASE}/logs"):
        os.makedirs(f"{env_config.APP_BASE}/logs")

    with ConfigDao() as dao:
        config = dao.get_active()
        if not config:
            install()
        if "main" in env_config.NODE_ROLE:
            config = dao.get_active()
                
            if "cluster_id" not in config:
                dao.update_by_id(config["_id"], {"cluster_id": f"{gen_random_string(64)}"})
            schedule.every().day.at(env_config.MAINTENANCE_WINDOW).do(ClusterTool.update)
            schedule.every().hour.do(ClusterTool.clean)
            schedule.every(60).seconds.do(LogArchiverTool.auto_archive)
            schedule.every(10).seconds.do(JailTool.calc_process_jails)
            schedule.every(30).seconds.do(ClusterTool.auto_apply_config)
            ClusterTool.clean()
        else:
            schedule.every(10).seconds.do(ClusterTool.auto_replicate_config)
        schedule.every(10).seconds.do(ClusterTool().node_monitor)
    
        try:
            ClusterTool.apply_config(reconfigure=True)
        except Exception as e:
            app.logger.error(f"Failed to apply configuration: {e}")
            app.logger.error(traceback.format_exc())

    scheduler_thread = threading.Thread(target=_scheduler, daemon=True)
    scheduler_thread.start()
