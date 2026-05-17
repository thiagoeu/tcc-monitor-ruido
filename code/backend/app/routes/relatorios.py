from flask import Response, jsonify, request

from app.database import utc_now_iso
from app.services import (
    build_text_report,
    get_report_summary,
)

from . import main_bp


def parse_int(value, default, min_value, max_value):
    try:
        parsed = int(value)

    except (TypeError, ValueError):
        parsed = default

    return max(min_value, min(max_value, parsed))


@main_bp.route("/api/relatorios/resumo", methods=["GET"])
def http_relatorio_resumo():
    hours = parse_int(
        request.args.get("hours", 24),
        24,
        1,
        24 * 30,
    )

    return jsonify(get_report_summary(hours))


@main_bp.route("/api/relatorios/txt", methods=["GET"])
def http_relatorio_txt():
    hours = parse_int(
        request.args.get("hours", 24),
        24,
        1,
        24 * 30,
    )

    summary = get_report_summary(hours)

    content = build_text_report(summary)

    timestamp = utc_now_iso().replace(":", "-").split("+")[0]

    filename = f"relatorio_ruido_{timestamp}.txt"

    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


@main_bp.route("/api/relatorios/resumo", methods=["OPTIONS"])
@main_bp.route("/api/relatorios/txt", methods=["OPTIONS"])
def relatorios_options():
    return ("", 204)