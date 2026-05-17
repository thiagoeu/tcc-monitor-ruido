from datetime import datetime, timedelta, timezone

from ..database import (
    get_connection,
    row_to_dict,
    utc_now_iso,
)
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
