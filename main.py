"""Main Flask application initialization and blueprint registration for NXGuard."""

import traceback

import nxcore.config as nxcore_config
from nxcore.controllers.base_controller import response_error_404, response_error_500
from nxcore.middleware.logging_manager import logger, LoggingManager
from nxcore.middleware.socket_manager import init_socketio
from nxcore.middleware.jwt_manager import JWTManager

from flask import Flask, Blueprint
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_restful import Api

import config
from api.routes import register as register_api_routes

nxcore_config.init(
    {
        "LOGLEVEL": config.LOGLEVEL,
        "JWT_SECRET_KEY": config.JWT_SECRET_KEY,
        "JWT_AUD": config.JWT_AUD,
        "SECURITY_ENABLED": config.SECURITY_ENABLED,
        "API_KEY": config.NXGUARD_API_KEY,
    }
)


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limite de 16MB

app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

LoggingManager(app)
JWTManager(app)

ma = Marshmallow()
ma.init_app(app)
socketio = init_socketio(app)
api = Api(app)
bp = Blueprint("gw", __name__, template_folder="templates")
register_api_routes(app, bp)
app.register_blueprint(bp)


@app.errorhandler(404)
def not_found_error(error):
    """Handles HTTP 404 Not Found errors."""
    return response_error_404()


@app.errorhandler(500)
def internal_error(error):
    """Handles HTTP 500 Internal Server errors."""
    stack_trace = traceback.format_exc()
    logger.error(f"500 Error: {error}, Stack Trace: {stack_trace}")
    return response_error_500("Unexpected Server Error", details=stack_trace)


@app.errorhandler(Exception)
def handle_exception(error):
    """Handles uncaught exceptions globally."""
    stack_trace = traceback.format_exc()
    logger.error(f"Internal Server Error: {stack_trace}")
    return response_error_500("Unexpected Server Error", details=stack_trace)
