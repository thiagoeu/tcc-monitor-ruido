from flask import current_app, jsonify
from app.database import utc_now_iso
from . import main_bp


@main_bp.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "monitor-ruido-backend",
            "database": current_app.config["DB_PATH"],
            "timestamp": utc_now_iso(),
        }
    )