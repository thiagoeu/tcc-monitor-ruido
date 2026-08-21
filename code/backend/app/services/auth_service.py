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

    if papel not in ("admin_master", "admin", "visualizador"):
        raise ValueError("papel deve ser 'admin_master', 'admin' ou 'visualizador'.")

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


def get_usuario(usuario_id):
    """Retorna um usuário pelo ID (dict público) ou None se não encontrado."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    connection.close()
    return _usuario_publico(row) if row else None


def update_usuario(usuario_id, payload):
    """
    Atualiza nome, email, papel e/ou ativo de um usuário.
    Levanta ValueError em payload inválido e RuntimeError em email duplicado.
    """
    nome = payload.get("nome")
    email = payload.get("email")
    papel = payload.get("papel")
    ativo = payload.get("ativo")

    # Validações
    if nome is not None:
        nome = str(nome).strip()
        if not nome:
            raise ValueError("nome não pode ser vazio.")

    if email is not None:
        email = str(email).strip().lower()
        if not email:
            raise ValueError("email não pode ser vazio.")

    if papel is not None:
        papel = str(papel).strip().lower()
        if papel not in ("admin_master", "admin", "visualizador"):
            raise ValueError("papel deve ser 'admin_master', 'admin' ou 'visualizador'.")

    if ativo is not None and ativo not in (0, 1, True, False):
        raise ValueError("ativo deve ser 0 ou 1.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        connection.close()
        return None

    # Verificar email duplicado (excluindo o próprio usuário)
    if email and email != row["email"]:
        cursor.execute(
            "SELECT id FROM usuarios WHERE email = ? AND id != ?",
            (email, usuario_id),
        )
        if cursor.fetchone():
            connection.close()
            raise RuntimeError("E-mail já cadastrado.")

    # Monta SET dinâmico apenas com campos fornecidos
    campos = {}
    if nome is not None:
        campos["nome"] = nome
    if email is not None:
        campos["email"] = email
    if papel is not None:
        campos["papel"] = papel
    if ativo is not None:
        campos["ativo"] = int(bool(ativo))

    if not campos:
        connection.close()
        return _usuario_publico(row)

    set_clause = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [usuario_id]
    cursor.execute(
        f"UPDATE usuarios SET {set_clause} WHERE id = ?",  # noqa: S608
        values,
    )
    connection.commit()

    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    updated = cursor.fetchone()
    connection.close()
    return _usuario_publico(updated)


def delete_usuario(usuario_id):
    """
    Soft-delete: marca ativo=0. Preserva dados históricos (medições, alertas).
    Retorna True se desativado, False se não encontrado.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usuarios SET ativo = 0 WHERE id = ? AND ativo = 1",
        (usuario_id,),
    )
    connection.commit()
    affected = cursor.rowcount
    connection.close()
    return affected > 0


def change_senha(usuario_id, nova_senha, senha_atual=None, is_admin=False):
    """
    Troca a senha de um usuário.
    - Se is_admin=True, não exige senha_atual (acesso privilegiado do admin).
    - Se is_admin=False, valida senha_atual antes de trocar.
    Levanta ValueError se nova_senha for vazia, AuthError se senha_atual incorreta.
    """
    nova_senha = str(nova_senha).strip()
    if len(nova_senha) < 6:
        raise ValueError("A nova senha deve ter pelo menos 6 caracteres.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id = ? AND ativo = 1", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        connection.close()
        return False

    if not is_admin:
        if not senha_atual:
            connection.close()
            raise ValueError("Senha atual é obrigatória.")
        if not check_password_hash(row["senha_hash"], senha_atual):
            connection.close()
            raise PermissionError("Senha atual incorreta.")

    cursor.execute(
        "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
        (generate_password_hash(nova_senha), usuario_id),
    )
    connection.commit()
    connection.close()
    return True