import sqlite3

from ..database import (
    get_connection,
    row_to_dict,
    utc_now_iso,
)


def create_medicao(payload):
    sensor_id = str(payload.get("sensor_id", "")).strip()
    db = payload.get("db")

    if not sensor_id:
        raise ValueError("sensor_id é obrigatório.")

    try:
        db = float(db)
    except (TypeError, ValueError):
        raise ValueError("db deve ser numérico.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM ambientes WHERE sensor_id = ? AND ativo = 1", (sensor_id,))
    ambiente = cursor.fetchone()
    if not ambiente:
        connection.close()
        return None

    excedeu_limite = 1 if db > ambiente["limite_db"] else 0
    timestamp = utc_now_iso()

    cursor.execute(
        """
        INSERT INTO medicoes (ambiente_id, db, excedeu_limite, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (ambiente["id"], db, excedeu_limite, timestamp),
    )
    medicao_id = cursor.lastrowid

    alerta_criado = False
    if excedeu_limite:
        mensagem = f"Ruído acima do limite em {ambiente['nome']}: {db:.1f} dB"
        cursor.execute(
            """
            INSERT INTO alertas (ambiente_id, medicao_id, mensagem, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (ambiente["id"], medicao_id, mensagem, timestamp),
        )
        alerta_criado = True

    connection.commit()
    connection.close()

    return {
        "ok": True,
        "ambiente_id": ambiente["id"],
        "sensor_id": sensor_id,
        "db": db,
        "limite_db": ambiente["limite_db"],
        "excedeu_limite": bool(excedeu_limite),
        "alerta_criado": alerta_criado,
        "timestamp": timestamp,
    }


def list_alertas(limit):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT al.id, al.ambiente_id, a.nome AS ambiente_nome, al.medicao_id,
               al.mensagem, al.created_at
        FROM alertas al
        JOIN ambientes a ON a.id = al.ambiente_id
        ORDER BY al.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [row_to_dict(row) for row in rows]
