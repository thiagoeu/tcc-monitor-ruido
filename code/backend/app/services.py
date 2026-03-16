import sqlite3
from datetime import datetime, timedelta, timezone

from .database import get_connection, row_to_dict, utc_now_iso


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


def get_report_summary(hours):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_iso = since.isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT a.id, a.nome, a.localizacao, a.sensor_id, a.limite_db,
               COUNT(m.id) AS total_medicoes,
               COALESCE(SUM(m.excedeu_limite), 0) AS total_alertas,
               AVG(m.db) AS media_db,
               MAX(m.db) AS pico_db,
               MIN(m.db) AS minimo_db
        FROM ambientes a
        LEFT JOIN medicoes m ON m.ambiente_id = a.id AND m.created_at >= ?
        GROUP BY a.id, a.nome, a.localizacao, a.sensor_id, a.limite_db
        ORDER BY a.id ASC
        """,
        (since_iso,),
    )
    rows = [row_to_dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT COUNT(*) AS total_medicoes,
               COALESCE(SUM(excedeu_limite), 0) AS total_alertas,
               AVG(db) AS media_db,
               MAX(db) AS pico_db,
               MIN(db) AS minimo_db
        FROM medicoes
        WHERE created_at >= ?
        """,
        (since_iso,),
    )
    overall = row_to_dict(cursor.fetchone())

    connection.close()

    total_medicoes = int(overall["total_medicoes"] or 0)
    total_alertas = int(overall["total_alertas"] or 0)
    percentual_alerta = (total_alertas / total_medicoes * 100) if total_medicoes else 0.0

    ambientes = []
    for row in rows:
        amb_total = int(row["total_medicoes"] or 0)
        amb_alertas = int(row["total_alertas"] or 0)
        amb_percentual = (amb_alertas / amb_total * 100) if amb_total else 0.0
        ambientes.append(
            {
                "id": row["id"],
                "nome": row["nome"],
                "localizacao": row["localizacao"],
                "sensor_id": row["sensor_id"],
                "limite_db": row["limite_db"],
                "total_medicoes": amb_total,
                "total_alertas": amb_alertas,
                "percentual_alerta": round(amb_percentual, 2),
                "media_db": round(float(row["media_db"]), 2) if row["media_db"] is not None else None,
                "pico_db": round(float(row["pico_db"]), 2) if row["pico_db"] is not None else None,
                "minimo_db": round(float(row["minimo_db"]), 2) if row["minimo_db"] is not None else None,
            }
        )

    return {
        "janela_horas": hours,
        "gerado_em": utc_now_iso(),
        "geral": {
            "total_medicoes": total_medicoes,
            "total_alertas": total_alertas,
            "percentual_alerta": round(percentual_alerta, 2),
            "media_db": round(float(overall["media_db"]), 2) if overall["media_db"] is not None else None,
            "pico_db": round(float(overall["pico_db"]), 2) if overall["pico_db"] is not None else None,
            "minimo_db": round(float(overall["minimo_db"]), 2) if overall["minimo_db"] is not None else None,
        },
        "ambientes": ambientes,
    }


def build_text_report(summary):
    lines = [
        "Relatório de Monitoramento de Ruído",
        f"Gerado em: {summary['gerado_em']}",
        f"Janela de análise: últimas {summary['janela_horas']} hora(s)",
        "",
        "Resumo Geral",
        f"- Total de medições: {summary['geral']['total_medicoes']}",
        f"- Total de alertas: {summary['geral']['total_alertas']}",
        f"- Percentual de alerta: {summary['geral']['percentual_alerta']:.2f}%",
        f"- Média dB: {summary['geral']['media_db'] if summary['geral']['media_db'] is not None else '-'}",
        f"- Pico dB: {summary['geral']['pico_db'] if summary['geral']['pico_db'] is not None else '-'}",
        f"- Mínimo dB: {summary['geral']['minimo_db'] if summary['geral']['minimo_db'] is not None else '-'}",
        "",
        "Ambientes",
    ]

    if not summary["ambientes"]:
        lines.append("- Sem dados de ambientes")
    else:
        for ambiente in summary["ambientes"]:
            lines.extend(
                [
                    "",
                    f"{ambiente['nome']} ({ambiente['sensor_id']})",
                    f"  Localização: {ambiente['localizacao']}",
                    f"  Limite: {ambiente['limite_db']} dB",
                    f"  Medições: {ambiente['total_medicoes']}",
                    f"  Alertas: {ambiente['total_alertas']}",
                    f"  Percentual de alerta: {ambiente['percentual_alerta']:.2f}%",
                    f"  Média dB: {ambiente['media_db'] if ambiente['media_db'] is not None else '-'}",
                    f"  Pico dB: {ambiente['pico_db'] if ambiente['pico_db'] is not None else '-'}",
                    f"  Mínimo dB: {ambiente['minimo_db'] if ambiente['minimo_db'] is not None else '-'}",
                ]
            )

    return "\n".join(lines) + "\n"
