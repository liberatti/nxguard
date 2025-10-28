from flask import  render_template, current_app

routes = [
    
]

def register(app,bp):
    @bp.route("/")
    def index():
        return render_template("index.html")

    @bp.route("/<path:path>")
    def catch_all(path: str):       
        if "." in path and not path.endswith("/"):
            try:
                return current_app.send_static_file(path)
            except:
                pass
        return render_template("index.html")
    for route, url_prefix in routes:
        app.register_blueprint(route, url_prefix=url_prefix)