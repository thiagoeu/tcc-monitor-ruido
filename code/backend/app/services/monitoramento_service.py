import sqlite3

from ..database import (
    get_connection,
    row_to_dict,
    utc_now_iso,
)

def get_monitoramento(limit):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM ambientes ORDER BY id ASC")
    ambientes = [row_to_dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT m.id, m.ambiente_id, a.nome AS ambiente_nome, a.sensor_id,
               a.limite_db, m.db, m.excedeu_limite, m.created_at
        FROM medicoes m
        JOIN ambientes a ON a.id = m.ambiente_id
        ORDER BY m.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    medicoes = [row_to_dict(row) for row in cursor.fetchall()]

    latest_by_ambiente = {}
    for medicao in medicoes:
        if medicao["ambiente_id"] not in latest_by_ambiente:
            latest_by_ambiente[medicao["ambiente_id"]] = medicao

    cursor.execute(
        """
        SELECT al.id, al.ambiente_id, al.medicao_id, al.mensagem, al.created_at,
               a.nome AS ambiente_nome
        FROM alertas al
        JOIN ambientes a ON a.id = al.ambiente_id
        ORDER BY al.id DESC
        LIMIT 20
        """
    )
    alertas = [row_to_dict(row) for row in cursor.fetchall()]

    connection.close()

    return {
        "ambientes": ambientes,
        "ultima_por_ambiente": latest_by_ambiente,
        "medicoes": medicoes,
        "alertas": alertas,
        "servidor_em": utc_now_iso(),
    }
