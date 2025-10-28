import os
import threading
import time
import traceback

import schedule
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_restful import Api

import basic4web.config as basic4web_config
import config as env_config
from api.routes import register as register_api_routes
from basic4web.controllers.base_controller import response_error_404, response_error_500
from basic4web.middleware.logging import logger
from basic4web.middleware.socket_manager import init_socketio

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limite de 16MB

cors = CORS(resources={r"/*": {"origins": "*"}})
# cors = CORS(resources=env_config.CORS)
cors.init_app(app)

ma = Marshmallow()
ma.init_app(app)

socketio = init_socketio(app)

api = Api(app)

bp = Blueprint("gw", __name__, template_folder="templates")
register_api_routes(app, bp)
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
    basic4web_config.init({
        "LOG_LEVEL": 'DEBUG',
        'JWT_SECRET_KEY': 'nxguard-dev'
    })

    if not os.path.exists(f"{env_config.APP_BASE}/logs"):
        os.makedirs(f"{env_config.APP_BASE}/logs")

    scheduler_thread = threading.Thread(target=_scheduler, daemon=True)
    scheduler_thread.start()
