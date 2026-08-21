import csv
import io
import math
from datetime import datetime, timedelta, timezone

from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ..database import (
    get_connection,
    row_to_dict,
    utc_now_iso,
)

def calculate_leq(db_values):
    if not db_values:
        return 0.0
    sum_pow = sum(math.pow(10, db / 10.0) for db in db_values)
    return 10.0 * math.log10(sum_pow / len(db_values))

def calculate_median(db_values):
    if not db_values:
        return 0.0
    s = sorted(db_values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2.0

def get_report_summary(hours):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_iso = since.isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    # Get all medições in window to compute Leq, Median and chart
    cursor.execute(
        """
        SELECT m.ambiente_id, m.db, m.created_at, m.excedeu_limite,
               a.nome as ambiente_nome, a.localizacao, a.sensor_id, a.limite_db
        FROM medicoes m
        JOIN ambientes a ON m.ambiente_id = a.id
        WHERE m.created_at >= ?
        ORDER BY m.created_at ASC
        """,
        (since_iso,),
    )
    all_medicoes = [row_to_dict(r) for r in cursor.fetchall()]

    # Also need all ambientes even if they have 0 medições
    cursor.execute("SELECT id, nome, localizacao, sensor_id, limite_db FROM ambientes ORDER BY id ASC")
    all_ambientes = [row_to_dict(r) for r in cursor.fetchall()]

    connection.close()

    total_medicoes = len(all_medicoes)
    total_alertas = sum(1 for m in all_medicoes if m["excedeu_limite"])
    percentual_alerta = (total_alertas / total_medicoes * 100) if total_medicoes else 0.0
    
    all_dbs = [float(m["db"]) for m in all_medicoes]
    overall_media = sum(all_dbs) / total_medicoes if total_medicoes else None
    overall_pico = max(all_dbs) if total_medicoes else None
    overall_minimo = min(all_dbs) if total_medicoes else None
    overall_mediana = calculate_median(all_dbs) if total_medicoes else None
    overall_leq = calculate_leq(all_dbs) if total_medicoes else None

    ambientes_summary = []
    
    for amb in all_ambientes:
        amb_id = amb["id"]
        amb_meds = [m for m in all_medicoes if m["ambiente_id"] == amb_id]
        amb_dbs = [float(m["db"]) for m in amb_meds]
        
        amb_total = len(amb_meds)
        amb_alertas = sum(1 for m in amb_meds if m["excedeu_limite"])
        amb_percentual = (amb_alertas / amb_total * 100) if amb_total else 0.0
        
        ambientes_summary.append({
            "id": amb_id,
            "nome": amb["nome"],
            "localizacao": amb["localizacao"],
            "sensor_id": amb["sensor_id"],
            "limite_db": amb["limite_db"],
            "total_medicoes": amb_total,
            "total_alertas": amb_alertas,
            "percentual_alerta": round(amb_percentual, 2),
            "media_db": round(sum(amb_dbs) / amb_total, 2) if amb_total else None,
            "mediana_db": round(calculate_median(amb_dbs), 2) if amb_total else None,
            "leq_db": round(calculate_leq(amb_dbs), 2) if amb_total else None,
            "pico_db": round(max(amb_dbs), 2) if amb_total else None,
            "minimo_db": round(min(amb_dbs), 2) if amb_total else None,
        })

    return {
        "janela_horas": hours,
        "gerado_em": utc_now_iso(),
        "geral": {
            "total_medicoes": total_medicoes,
            "total_alertas": total_alertas,
            "percentual_alerta": round(percentual_alerta, 2),
            "media_db": round(overall_media, 2) if overall_media is not None else None,
            "mediana_db": round(overall_mediana, 2) if overall_mediana is not None else None,
            "leq_db": round(overall_leq, 2) if overall_leq is not None else None,
            "pico_db": round(overall_pico, 2) if overall_pico is not None else None,
            "minimo_db": round(overall_minimo, 2) if overall_minimo is not None else None,
        },
        "ambientes": ambientes_summary,
        "_raw_medicoes": all_medicoes # Internal use for charts
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
        f"- Leq dB(A): {summary['geral']['leq_db'] if summary['geral']['leq_db'] is not None else '-'}",
        f"- Média dB: {summary['geral']['media_db'] if summary['geral']['media_db'] is not None else '-'}",
        f"- Mediana dB: {summary['geral']['mediana_db'] if summary['geral']['mediana_db'] is not None else '-'}",
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
                    f"  Leq dB(A): {ambiente['leq_db'] if ambiente['leq_db'] is not None else '-'}",
                    f"  Média dB: {ambiente['media_db'] if ambiente['media_db'] is not None else '-'}",
                    f"  Mediana dB: {ambiente['mediana_db'] if ambiente['mediana_db'] is not None else '-'}",
                    f"  Pico dB: {ambiente['pico_db'] if ambiente['pico_db'] is not None else '-'}",
                    f"  Mínimo dB: {ambiente['minimo_db'] if ambiente['minimo_db'] is not None else '-'}",
                ]
            )

    return "\n".join(lines) + "\n"

def build_csv_report(summary):
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Ambiente", "Sensor ID", "Localizacao", "Limite dB", "Total Medicoes", "Total Alertas", "% Alerta", "Leq dB(A)", "Media dB", "Mediana dB", "Pico dB", "Minimo dB"])
    
    for amb in summary.get("ambientes", []):
        writer.writerow([
            amb["nome"],
            amb["sensor_id"],
            amb["localizacao"],
            amb["limite_db"],
            amb["total_medicoes"],
            amb["total_alertas"],
            f"{amb['percentual_alerta']}%",
            amb["leq_db"] if amb["leq_db"] is not None else "",
            amb["media_db"] if amb["media_db"] is not None else "",
            amb["mediana_db"] if amb["mediana_db"] is not None else "",
            amb["pico_db"] if amb["pico_db"] is not None else "",
            amb["minimo_db"] if amb["minimo_db"] is not None else ""
        ])
        
    return output.getvalue()

def build_pdf_report(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    
    pdf.cell(0, 10, "Relatorio de Monitoramento de Ruido", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"Gerado em: {summary['gerado_em']}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, f"Janela de analise: ultimas {summary['janela_horas']} hora(s)", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(5)
    
    # Resumo Geral
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Resumo Geral", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    
    g = summary["geral"]
    pdf.cell(0, 6, f"Total de medicoes: {g['total_medicoes']} | Total de alertas: {g['total_alertas']} ({g['percentual_alerta']}%)", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Leq dB(A): {g['leq_db'] or '-'} | Media dB: {g['media_db'] or '-'} | Mediana dB: {g['mediana_db'] or '-'}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Pico dB: {g['pico_db'] or '-'} | Minimo dB: {g['minimo_db'] or '-'}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    
    # Chart
    medicoes = summary.get("_raw_medicoes", [])
    if medicoes:
        # Group by ambient
        plt.figure(figsize=(8, 4))
        ambientes_data = {}
        for m in medicoes:
            nome = m["ambiente_nome"]
            if nome not in ambientes_data:
                ambientes_data[nome] = {"times": [], "dbs": []}
            # Parse time safely
            dt = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
            ambientes_data[nome]["times"].append(dt)
            ambientes_data[nome]["dbs"].append(float(m["db"]))
            
        for nome, data in ambientes_data.items():
            plt.plot(data["times"], data["dbs"], label=nome, alpha=0.7)
            
        plt.title("Nivel de Ruido no Tempo")
        plt.ylabel("dB(A)")
        plt.xlabel("Tempo")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="upper right", fontsize='small')
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        plt.close()
        
        pdf.image(buf, x=15, w=180)
        pdf.ln(5)
        
    # Ambientes
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Detalhes por Ambiente", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    for amb in summary.get("ambientes", []):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, f"{amb['nome']} ({amb['sensor_id']})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9)
        pdf.cell(0, 6, f"Limite: {amb['limite_db']} dB | Localizacao: {amb['localizacao']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Medicoes: {amb['total_medicoes']} | Alertas: {amb['total_alertas']} ({amb['percentual_alerta']}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Leq dB(A): {amb['leq_db'] or '-'} | Media dB: {amb['media_db'] or '-'} | Mediana dB: {amb['mediana_db'] or '-'}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Pico dB: {amb['pico_db'] or '-'} | Minimo dB: {amb['minimo_db'] or '-'}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    return bytes(pdf.output())
