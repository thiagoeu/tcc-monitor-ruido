from flask import current_app, send_from_directory

from . import main_bp


@main_bp.route("/", methods=["GET"])
def dashboard():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "index.html")


@main_bp.route("/graficos", methods=["GET"])
def graficos():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "graficos.html")


@main_bp.route("/graficos.html", methods=["GET"])
def graficos_html():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "graficos.html")


@main_bp.route("/assets/<path:filename>", methods=["GET"])
def frontend_assets(filename):
    return send_from_directory(
        current_app.config["FRONTEND_ASSETS_DIR"],
        filename,
    )