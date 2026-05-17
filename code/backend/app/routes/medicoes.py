from flask import jsonify, request

from app.services import (
    create_medicao,
    get_monitoramento,
    list_alertas,
)

from . import main_bp


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


@main_bp.route("/api/medicoes", methods=["POST"])
def http_create_medicao():
    payload = request.get_json(silent=True) or {}

    try:
        result = create_medicao(payload)

    except ValueError as exc:
        return json_error(str(exc), 400)

    if not result:
        return json_error(
            "sensor_id não encontrado ou ambiente inativo.",
            404,
        )

    return jsonify(result)


@main_bp.route("/api/monitoramento", methods=["GET"])
def http_monitoramento():
    limit = parse_int(
        request.args.get("limit", 60),
        60,
        1,
        400,
    )

    return jsonify(get_monitoramento(limit))


@main_bp.route("/api/alertas", methods=["GET"])
def http_alertas():
    limit = parse_int(
        request.args.get("limit", 50),
        50,
        1,
        500,
    )

    return jsonify(list_alertas(limit))


@main_bp.route("/api/medicoes", methods=["OPTIONS"])
@main_bp.route("/api/monitoramento", methods=["OPTIONS"])
@main_bp.route("/api/alertas", methods=["OPTIONS"])
def medicoes_options():
    return ("", 204)