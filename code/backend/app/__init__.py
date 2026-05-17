from pathlib import Path

from flask import Flask

from .database import init_db, seed_default_environments
from .routes import main_bp


def create_app():
    base_dir = Path(__file__).resolve().parent.parent
    project_dir = base_dir.parent
    frontend_dir = project_dir / "frontend"
    frontend_assets_dir = frontend_dir / "assets"
    db_path = Path(base_dir / "ruido.db")

    app = Flask(__name__)
    app.config.update(
        {
            "DB_PATH": str(db_path),
            "FRONTEND_DIR": str(frontend_dir),
            "FRONTEND_ASSETS_DIR": str(frontend_assets_dir),
        }
    )

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    app.register_blueprint(main_bp)

    with app.app_context():
        init_db()
        seed_default_environments()

    return app
