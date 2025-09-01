from flask import  render_template, send_from_directory, current_app
import os
from api.controller.oauth_controller import routes as oauth_routes
from api.controller.certificate_controller import routes as certificate_routes
from api.controller.challenge_controller import routes as acme_routes
from api.controller.cluster_controller import routes as cluster_routes
from api.controller.feed_controller import routes as feed_routes
from api.controller.jail_controller import routes as jail_routes
from api.controller.oauth_controller import routes as oauth_routes
from api.controller.replica_controller import routes as replica_routes
from api.controller.route_filter_controller import routes as route_filter_routes
from api.controller.rulecat_controller import routes as rule_cat_routes
from api.controller.rulesec_controller import routes as rule_sec_routes
from api.controller.sensor_controller import routes as sensor_routes
from api.controller.service_controller import routes as service_routes
from api.controller.transaction_controller import routes as trn_routes
from api.controller.upstream_controller import routes as upstream_routes
from api.controller.user_controller import routes as user_routes

routes = [
    (user_routes, "/api/user"),
    (upstream_routes, "/api/upstream"),
    (rule_cat_routes, "/api/rulecat"),
    (rule_sec_routes, "/api/rulesec"),
    (feed_routes, "/api/feed"),
    (certificate_routes, "/api/certificate"),
    (sensor_routes, "/api/sensor"),
    (service_routes, "/api/service"),
    (cluster_routes, "/api/cluster"),
    (replica_routes, "/api/replica"),
    (trn_routes, "/api/trn"),
    (jail_routes, "/api/jail"),
    (route_filter_routes, "/api/route_filter"),
    (acme_routes, "/.well-known"),
    (oauth_routes, "/api/oauth"),
]

def register(app,bp):

    @bp.route("/api-docs")
    def api_docs():
        """Serve the API documentation page."""
        return send_from_directory(current_app.static_folder, "swagger-ui/index.html")

    @bp.route("/openapi.yml")
    def openapi_spec():
        """Serve the OpenAPI specification file."""
        return send_from_directory(current_app.static_folder, "swagger-ui/openapi.yml")

    @bp.route("/")
    def index():
        return render_template("index.html")

    @bp.route("/<path:path>")
    def catch_all(path: str):       
        # Verificar se é um arquivo estático
        if "." in path and not path.endswith("/"):
            # Tentar servir como arquivo estático
            try:
                return current_app.send_static_file(path)
            except:
                # Se não conseguir servir o arquivo estático, retorna o index.html
                pass
        
        # Para todas as outras rotas, retorna o index.html (SPA routing)
        return render_template("index.html")
            
    for route, url_prefix in routes:
        app.register_blueprint(route, url_prefix=url_prefix)