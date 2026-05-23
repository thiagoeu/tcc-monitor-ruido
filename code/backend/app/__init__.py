from pathlib import Path
from flask import Flask, send_from_directory
from .database import init_db, seed_default_environments
from .routes import main_bp


def create_app():
    base_dir = Path(__file__).resolve().parent.parent   # backend/
    project_dir = base_dir.parent                       # code/
    frontend_dir = project_dir / "frontend"             # code/frontend/
    db_path = base_dir / "ruido.db"

    # Cria o app servindo a pasta frontend como estática na raiz
    app = Flask(__name__,
                static_folder=str(frontend_dir),
                static_url_path='')

    app.config.update({
        "DB_PATH": str(db_path),
        "FRONTEND_DIR": str(frontend_dir),
    })

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    # Rota raiz usando o caminho direto (evita erro de tipo)
    @app.route('/')
    def index():
        return send_from_directory(str(frontend_dir), 'index.html')

    app.register_blueprint(main_bp)

    with app.app_context():
        init_db()
        seed_default_environments()

    return app