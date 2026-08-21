from functools import wraps

from flask import g, jsonify, request

from app.services import (
    autenticar_por_token,
    change_senha,
    create_usuario,
    delete_usuario,
    get_usuario,
    list_usuarios,
    login,
    logout,
    update_usuario,
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
    """Permite acesso a usuários com papel 'admin' OU 'admin_master'."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extrair_token()
        usuario = autenticar_por_token(token) if token else None
        if not usuario:
            return json_error("Autenticação necessária.", 401)
        if usuario["papel"] not in ("admin", "admin_master"):
            return json_error("Acesso restrito ao administrador.", 403)
        g.usuario = usuario
        return view(*args, **kwargs)

    return wrapped


def _is_admin_level(papel):
    """Retorna True se o papel é de nível administrativo (admin ou admin_master)."""
    return papel in ("admin", "admin_master")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Usuários — listagem e criação (admin)
# ---------------------------------------------------------------------------

@main_bp.route("/api/usuarios", methods=["GET"])
@admin_required
def http_list_usuarios():
    return jsonify(list_usuarios())


@main_bp.route("/api/usuarios", methods=["POST"])
@admin_required
def http_create_usuario():
    payload = request.get_json(silent=True) or {}

    # admin (não master) só pode criar visualizadores
    papel_solicitado = str(payload.get("papel", "")).strip().lower()
    if g.usuario["papel"] == "admin" and _is_admin_level(papel_solicitado):
        return json_error("Admin não pode criar usuários com papel administrativo.", 403)

    try:
        created = create_usuario(payload)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    response = jsonify(created)
    response.status_code = 201
    return response


# ---------------------------------------------------------------------------
# Usuários — detalhe, edição e exclusão (admin)
# ---------------------------------------------------------------------------

@main_bp.route("/api/usuarios/<int:usuario_id>", methods=["GET"])
@admin_required
def http_get_usuario(usuario_id):
    usuario = get_usuario(usuario_id)
    if not usuario:
        return json_error("Usuário não encontrado.", 404)
    return jsonify(usuario)


@main_bp.route("/api/usuarios/<int:usuario_id>", methods=["PUT"])
@admin_required
def http_update_usuario(usuario_id):
    payload = request.get_json(silent=True) or {}

    # admin (não master) não pode editar usuários de nível admin
    if g.usuario["papel"] == "admin":
        alvo = get_usuario(usuario_id)
        if alvo and _is_admin_level(alvo["papel"]):
            return json_error("Admin não pode editar usuários administrativos.", 403)
        # Nem promover a papel administrativo
        papel_solicitado = str(payload.get("papel", "")).strip().lower()
        if papel_solicitado and _is_admin_level(papel_solicitado):
            return json_error("Admin não pode promover usuários a papel administrativo.", 403)

    try:
        updated = update_usuario(usuario_id, payload)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    if updated is None:
        return json_error("Usuário não encontrado.", 404)

    return jsonify(updated)


@main_bp.route("/api/usuarios/<int:usuario_id>", methods=["DELETE"])
@admin_required
def http_delete_usuario(usuario_id):
    # Ninguém desativa a própria conta
    if g.usuario["id"] == usuario_id:
        return json_error("Você não pode desativar a sua própria conta.", 400)

    # admin (não master) não pode desativar usuários administrativos
    if g.usuario["papel"] == "admin":
        alvo = get_usuario(usuario_id)
        if alvo and _is_admin_level(alvo["papel"]):
            return json_error("Admin não pode desativar usuários administrativos.", 403)

    deleted = delete_usuario(usuario_id)
    if not deleted:
        return json_error("Usuário não encontrado ou já inativo.", 404)

    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Troca de senha
# ---------------------------------------------------------------------------

@main_bp.route("/api/usuarios/<int:usuario_id>/senha", methods=["PUT"])
@login_required
def http_change_senha(usuario_id):
    """
    admin_master e admin podem trocar senha sem informar a atual.
    admin só pode trocar senha de visualizadores.
    Usuário comum só pode trocar a própria senha e precisa informar a atual.
    """
    payload = request.get_json(silent=True) or {}
    nova_senha = str(payload.get("nova_senha", "")).strip()

    if not nova_senha:
        return json_error("Campo obrigatório: nova_senha.", 400)

    papel_req = g.usuario["papel"]
    is_admin_any = _is_admin_level(papel_req)

    # Não-admin só pode alterar a própria senha
    if not is_admin_any and g.usuario["id"] != usuario_id:
        return json_error("Acesso negado.", 403)

    # admin (não master) não pode alterar senha de usuários administrativos
    if papel_req == "admin" and g.usuario["id"] != usuario_id:
        alvo = get_usuario(usuario_id)
        if alvo and _is_admin_level(alvo["papel"]):
            return json_error("Admin não pode alterar senha de usuários administrativos.", 403)

    senha_atual = payload.get("senha_atual") if not is_admin_any else None

    try:
        ok = change_senha(
            usuario_id,
            nova_senha=nova_senha,
            senha_atual=senha_atual,
            is_admin=is_admin_any,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    except PermissionError as exc:
        return json_error(str(exc), 401)

    if not ok:
        return json_error("Usuário não encontrado.", 404)

    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# OPTIONS (CORS preflight)
# ---------------------------------------------------------------------------

@main_bp.route("/api/auth/login", methods=["OPTIONS"])
@main_bp.route("/api/auth/logout", methods=["OPTIONS"])
@main_bp.route("/api/auth/me", methods=["OPTIONS"])
@main_bp.route("/api/usuarios", methods=["OPTIONS"])
@main_bp.route("/api/usuarios/<int:usuario_id>", methods=["OPTIONS"])
@main_bp.route("/api/usuarios/<int:usuario_id>/senha", methods=["OPTIONS"])
def auth_options(**_kwargs):
    return ("", 204)