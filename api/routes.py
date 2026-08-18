from flask import render_template, current_app

import config
from api.controller.certificate_controller import routes as certificate_routes
from api.controller.challenge_controller import routes as challenge_routes
from api.controller.config_controller import routes as config_routes
from api.controller.feed_controller import routes as feed_routes
from api.controller.oauth_controller import routes as oauth_routes
from api.controller.replica_controller import routes as replica_routes
from api.controller.route_controller import routes as route_routes
from api.controller.rulecat_controller import routes as rulecat_routes
from api.controller.rulesec_controller import routes as rulesec_routes
from api.controller.sensor_controller import routes as sensor_routes
from api.controller.service_controller import routes as service_routes
from api.controller.transaction_controller import routes as transaction_routes
from api.controller.upstream_controller import routes as upstream_routes
from api.controller.user_controller import routes as user_routes

routes = [
    (certificate_routes, f"{config.APP_CONTEXT}/api/certificate"),
    (challenge_routes, f"{config.APP_CONTEXT}"),
    (config_routes, f"{config.APP_CONTEXT}/api/config"),
    (feed_routes, f"{config.APP_CONTEXT}/api/feed"),
    (oauth_routes, f"{config.APP_CONTEXT}/api/oauth"),
    (replica_routes, f"{config.APP_CONTEXT}/api/replica"),
    (route_routes, f"{config.APP_CONTEXT}/api/route"),
    (rulecat_routes, f"{config.APP_CONTEXT}/api/rulecat"),
    (rulesec_routes, f"{config.APP_CONTEXT}/api/rulesec"),
    (sensor_routes, f"{config.APP_CONTEXT}/api/sensor"),
    (service_routes, f"{config.APP_CONTEXT}/api/service"),
    (transaction_routes, f"{config.APP_CONTEXT}/api/trn"),
    (upstream_routes, f"{config.APP_CONTEXT}/api/upstream"),
    (user_routes, f"{config.APP_CONTEXT}/api/user"),
]


def register(app, bp):
    @bp.route("/")
    def index():
        return render_template("index.html")

    @bp.route("/<path:path>")
    def catch_all(path: str):
        context_prefix = config.APP_CONTEXT.strip("/")
        rel_path = path
        if context_prefix and (rel_path == context_prefix or rel_path.startswith(f"{context_prefix}/")):
            rel_path = rel_path[len(context_prefix):].lstrip("/")

        if "." in rel_path and not rel_path.endswith("/"):
            try:
                return current_app.send_static_file(rel_path)
            except Exception:
                pass
        return render_template("index.html")

    for route, url_prefix in routes:
        app.register_blueprint(route, url_prefix=url_prefix)
