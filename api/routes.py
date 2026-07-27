from flask import render_template, current_app

import config
from api.controller.config_controller import routes as config_routes
from api.controller.oauth_controller import routes as oauth_routes
from api.controller.upstream_controller import routes as upstream_routes

routes = [
    (upstream_routes, f"{config.APP_CONTEXT}/api/upstream"),
    (oauth_routes, f"{config.APP_CONTEXT}/api/oauth"),
    (config_routes, f"{config.APP_CONTEXT}/api/config"),
]


def register(app, bp):
    @bp.route("/")
    def index():
        return render_template("index.html")

    @bp.route("/<path:path>")
    def catch_all(path: str):
        if "." in path and not path.endswith("/"):
            try:
                return current_app.send_static_file(path)
            except Exception:
                pass
        return render_template("index.html")

    for route, url_prefix in routes:
        app.register_blueprint(route, url_prefix=url_prefix)
