from flask import Blueprint, Response, current_app, jsonify, request, send_from_directory

from app.database import utc_now_iso
from app.services import (
    build_text_report,
    create_ambiente,
    create_medicao,
    delete_ambiente,
    get_monitoramento,
    get_report_summary,
    list_alertas,
    list_ambientes,
    update_ambiente,
)

main_bp = Blueprint("main", __name__)


def json_error(message, status=400):
    response = jsonify({"erro": message})
    response.status_code = status
    return response


def parse_int(value, default, min_value, max_value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, min(max_value, parsed))


@main_bp.route("/", methods=["GET"])
def dashboard():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "index.html")


@main_bp.route("/graficos", methods=["GET"])
def graficos():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "graficos.html")


@main_bp.route("/graficos.html", methods=["GET"])
def graficos_html():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "graficos.html")


@main_bp.route("/assets/<path:filename>", methods=["GET"])
def frontend_assets(filename):
    return send_from_directory(current_app.config["FRONTEND_ASSETS_DIR"], filename)


@main_bp.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "monitor-ruido-backend",
            "database": current_app.config["DB_PATH"],
            "timestamp": utc_now_iso(),
        }
    )


@main_bp.route("/api/ambientes", methods=["GET"])
def http_list_ambientes():
    return jsonify(list_ambientes())


@main_bp.route("/api/ambientes", methods=["POST"])
def http_create_ambiente():
    payload = request.get_json(silent=True) or {}
    try:
        created = create_ambiente(payload)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    response = jsonify(created)
    response.status_code = 201
    return response


@main_bp.route("/api/ambientes/<int:ambiente_id>", methods=["PUT"])
def http_update_ambiente(ambiente_id):
    payload = request.get_json(silent=True) or {}
    try:
        updated = update_ambiente(ambiente_id, payload)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    if not updated:
        return json_error("Ambiente não encontrado.", 404)

    return jsonify(updated)


@main_bp.route("/api/ambientes/<int:ambiente_id>", methods=["DELETE"])
def http_delete_ambiente(ambiente_id):
    deleted = delete_ambiente(ambiente_id)
    if not deleted:
        return json_error("Ambiente não encontrado.", 404)

    return jsonify(
        {
            "ok": True,
            "mensagem": "Ambiente removido com sucesso.",
            "ambiente": deleted["ambiente"],
            "medicoes_removidas": deleted["medicoes_removidas"],
            "alertas_removidos": deleted["alertas_removidos"],
        }
    )


@main_bp.route("/api/medicoes", methods=["POST"])
def http_create_medicao():
    payload = request.get_json(silent=True) or {}
    try:
        result = create_medicao(payload)
    except ValueError as exc:
        return json_error(str(exc), 400)

    if not result:
        return json_error("sensor_id não encontrado ou ambiente inativo.", 404)

    return jsonify(result)


@main_bp.route("/api/monitoramento", methods=["GET"])
def http_monitoramento():
    limit = parse_int(request.args.get("limit", 60), 60, 1, 400)
    return jsonify(get_monitoramento(limit))


@main_bp.route("/api/alertas", methods=["GET"])
def http_alertas():
    limit = parse_int(request.args.get("limit", 50), 50, 1, 500)
    return jsonify(list_alertas(limit))


@main_bp.route("/api/relatorios/resumo", methods=["GET"])
def http_relatorio_resumo():
    hours = parse_int(request.args.get("hours", 24), 24, 1, 24 * 30)
    return jsonify(get_report_summary(hours))


@main_bp.route("/api/relatorios/txt", methods=["GET"])
def http_relatorio_txt():
    hours = parse_int(request.args.get("hours", 24), 24, 1, 24 * 30)
    summary = get_report_summary(hours)
    content = build_text_report(summary)
    timestamp = utc_now_iso().replace(":", "-").split("+")[0]
    filename = f"relatorio_ruido_{timestamp}.txt"

    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@main_bp.route("/api/medicoes", methods=["OPTIONS"])
@main_bp.route("/api/ambientes", methods=["OPTIONS"])
@main_bp.route("/api/ambientes/<int:ambiente_id>", methods=["OPTIONS"])
@main_bp.route("/api/monitoramento", methods=["OPTIONS"])
@main_bp.route("/api/alertas", methods=["OPTIONS"])
@main_bp.route("/api/relatorios/resumo", methods=["OPTIONS"])
@main_bp.route("/api/relatorios/txt", methods=["OPTIONS"])
def options_ok():
    return ("", 204)
