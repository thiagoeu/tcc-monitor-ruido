import sqlite3
from datetime import datetime, timedelta, timezone

from ..database import get_connection, row_to_dict, utc_now_iso


def create_ambiente(payload):
    nome = str(payload.get("nome", "")).strip()
    localizacao = str(payload.get("localizacao", "")).strip()
    sensor_id = str(payload.get("sensor_id", "")).strip()
    limite_db = payload.get("limite_db", 65)

    if not nome or not localizacao or not sensor_id:
        raise ValueError("Campos obrigatórios: nome, localizacao e sensor_id.")

    try:
        limite_db = float(limite_db)
    except (TypeError, ValueError):
        raise ValueError("limite_db deve ser numérico.")

    if limite_db < 0:
        raise ValueError("limite_db deve ser >= 0.")

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO ambientes (nome, localizacao, sensor_id, limite_db, ativo, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, localizacao, sensor_id, limite_db, 1, utc_now_iso()),
        )
        ambiente_id = cursor.lastrowid
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.close()
        raise RuntimeError("sensor_id já cadastrado.") from exc

    cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
    row = cursor.fetchone()
    connection.close()
    return row_to_dict(row)


def update_ambiente(ambiente_id, payload):
    fields = {}
    for key in ("nome", "localizacao", "sensor_id"):
        if key in payload:
            value = str(payload.get(key, "")).strip()
            if not value:
                raise ValueError(f"{key} não pode ser vazio.")
            fields[key] = value

    if "limite_db" in payload:
        try:
            limite_db = float(payload.get("limite_db"))
        except (TypeError, ValueError):
            raise ValueError("limite_db deve ser numérico.")
        if limite_db < 0:
            raise ValueError("limite_db deve ser >= 0.")
        fields["limite_db"] = limite_db

    if "ativo" in payload:
        fields["ativo"] = 1 if bool(payload.get("ativo")) else 0

    if not fields:
        raise ValueError("Nenhum campo válido para atualização.")

    set_clause = ", ".join([f"{field} = ?" for field in fields.keys()])
    values = list(fields.values()) + [ambiente_id]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM ambientes WHERE id = ?", (ambiente_id,))
    if not cursor.fetchone():
        connection.close()
        return None

    try:
        cursor.execute(f"UPDATE ambientes SET {set_clause} WHERE id = ?", values)
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.close()
        raise RuntimeError("sensor_id já cadastrado para outro ambiente.") from exc

    cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
    row = cursor.fetchone()
    connection.close()
    return row_to_dict(row)


def list_ambientes():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ambientes ORDER BY id ASC")
    rows = cursor.fetchall()
    connection.close()
    return [row_to_dict(row) for row in rows]


def delete_ambiente(ambiente_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM ambientes WHERE id = ?", (ambiente_id,))
    ambiente = cursor.fetchone()
    if not ambiente:
        connection.close()
        return None

    cursor.execute("DELETE FROM alertas WHERE ambiente_id = ?", (ambiente_id,))
    alertas_removidos = cursor.rowcount

    cursor.execute("DELETE FROM medicoes WHERE ambiente_id = ?", (ambiente_id,))
    medicoes_removidas = cursor.rowcount

    cursor.execute("DELETE FROM ambientes WHERE id = ?", (ambiente_id,))

    connection.commit()
    connection.close()

    return {
        "ambiente": row_to_dict(ambiente),
        "medicoes_removidas": medicoes_removidas,
        "alertas_removidos": alertas_removidos,
    }
