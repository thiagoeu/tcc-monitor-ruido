import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ..database import get_connection, row_to_dict, utc_now_iso


def _usuario_por_email(cursor, email):
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()


def _usuario_publico(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "papel": row["papel"],
        "ativo": row["ativo"],
        "created_at": row["created_at"],
        "last_login_at": row["last_login_at"],
    }


def _usuario_por_token(token):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE token = ? AND ativo = 1",
        (token,),
    )
    row = cursor.fetchone()
    connection.close()
    return row


def autenticar_por_token(token):
    """Retorna o usuário se o token for válido (não expirado), senão None."""
    row = _usuario_por_token(token)
    if not row:
        return None
    expira = datetime.fromisoformat(row["token_expira"])
    if expira <= datetime.now(timezone.utc):
        return None
    return _usuario_publico(row)


def login(email, senha):
    connection = get_connection()
    cursor = connection.cursor()

    row = _usuario_por_email(cursor, email)
    if not row or not row["ativo"]:
        connection.close()
        return None

    if not check_password_hash(row["senha_hash"], senha):
        connection.close()
        return None

    token = secrets.token_urlsafe(32)
    ttl_horas = current_app.config.get("TOKEN_TTL_HORAS", 168)
    expira = datetime.now(timezone.utc) + timedelta(hours=ttl_horas)

    cursor.execute(
        """
        UPDATE usuarios
        SET token = ?, token_expira = ?, last_login_at = ?
        WHERE id = ?
        """,
        (token, expira.isoformat(), utc_now_iso(), row["id"]),
    )
    connection.commit()
    connection.close()

    return {
        "token": token,
        "expira_em": expira.isoformat(),
        "usuario": _usuario_publico(row),
    }


def logout(token):
    if not token:
        return False
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usuarios SET token = NULL, token_expira = NULL WHERE token = ?",
        (token,),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount > 0


def create_usuario(payload):
    nome = str(payload.get("nome", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    senha = str(payload.get("senha", ""))
    papel = str(payload.get("papel", "visualizador")).strip().lower()

    if not nome or not email or not senha:
        raise ValueError("Campos obrigatórios: nome, email e senha.")

    if papel not in ("admin", "visualizador"):
        raise ValueError("papel deve ser 'admin' ou 'visualizador'.")

    connection = get_connection()
    cursor = connection.cursor()

    if _usuario_por_email(cursor, email):
        connection.close()
        raise RuntimeError("E-mail já cadastrado.")

    cursor.execute(
        """
        INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (nome, email, generate_password_hash(senha), papel, utc_now_iso()),
    )
    usuario_id = cursor.lastrowid
    connection.commit()

    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    connection.close()

    return _usuario_publico(row)


def list_usuarios():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY id ASC")
    rows = cursor.fetchall()
    connection.close()
    return [_usuario_publico(row) for row in rows]