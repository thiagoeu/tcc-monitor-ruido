from functools import wraps

from flask import g, jsonify, request

from app.services import (
    autenticar_por_token,
    create_usuario,
    list_usuarios,
    login,
    logout,
)

from . import main_bp


def json_error(message, status=400):
    response = jsonify({"erro": message})
    response.status_code = status
    return response


def _extrair_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extrair_token()
        usuario = autenticar_por_token(token) if token else None
        if not usuario:
            return json_error("Autenticação necessária.", 401)
        g.usuario = usuario
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extrair_token()
        usuario = autenticar_por_token(token) if token else None
        if not usuario:
            return json_error("Autenticação necessária.", 401)
        if usuario["papel"] != "admin":
            return json_error("Acesso restrito ao administrador.", 403)
        g.usuario = usuario
        return view(*args, **kwargs)

    return wrapped


@main_bp.route("/api/auth/login", methods=["POST"])
def http_login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    senha = str(payload.get("senha", ""))

    if not email or not senha:
        return json_error("Campos obrigatórios: email e senha.", 400)

    result = login(email, senha)
    if not result:
        return json_error("E-mail ou senha inválidos.", 401)

    return jsonify(result)


@main_bp.route("/api/auth/logout", methods=["POST"])
def http_logout():
    token = _extrair_token()
    logout(token)
    return jsonify({"ok": True})


@main_bp.route("/api/auth/me", methods=["GET"])
@login_required
def http_me():
    return jsonify(g.usuario)


@main_bp.route("/api/usuarios", methods=["GET"])
@admin_required
def http_list_usuarios():
    return jsonify(list_usuarios())


@main_bp.route("/api/usuarios", methods=["POST"])
@admin_required
def http_create_usuario():
    payload = request.get_json(silent=True) or {}

    try:
        created = create_usuario(payload)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    response = jsonify(created)
    response.status_code = 201
    return response


@main_bp.route("/api/auth/login", methods=["OPTIONS"])
@main_bp.route("/api/auth/logout", methods=["OPTIONS"])
@main_bp.route("/api/auth/me", methods=["OPTIONS"])
@main_bp.route("/api/usuarios", methods=["OPTIONS"])
def auth_options():
    return ("", 204)