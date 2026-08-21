from flask import jsonify, request

from app.services import (
    create_medicao,
    get_monitoramento,
    list_alertas,
    scan_sensores_fisicos,
)

from . import main_bp
from .auth import login_required


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


def parse_float(value, default, min_value, max_value):
    try:
        parsed = float(value)

    except (TypeError, ValueError):
        parsed = default

    return max(min_value, min(max_value, parsed))


def parse_registers(value):
    raw = str(value or "0,1")
    registers = []

    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            registers.append(int(chunk))
        except ValueError as exc:
            raise ValueError("registers deve conter apenas inteiros separados por virgula.") from exc

    if not registers:
        raise ValueError("registers deve conter ao menos um registrador.")

    return registers


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
@login_required
def http_monitoramento():
    limit = parse_int(
        request.args.get("limit", 60),
        60,
        1,
        400,
    )

    return jsonify(get_monitoramento(limit))


@main_bp.route("/api/alertas", methods=["GET"])
@login_required
def http_alertas():
    limit = parse_int(
        request.args.get("limit", 50),
        50,
        1,
        500,
    )

    return jsonify(list_alertas(limit))


@main_bp.route("/api/sensores/fisicos", methods=["GET"])
@login_required
def http_scan_sensores_fisicos():
    port = request.args.get("port", "/dev/serial0")
    baudrate = parse_int(request.args.get("baudrate", 9600), 9600, 300, 115200)
    start_id = parse_int(request.args.get("start_id", 1), 1, 1, 247)
    end_id = parse_int(request.args.get("end_id", 32), 32, 1, 247)
    function_code = parse_int(request.args.get("function_code", 3), 3, 3, 4)
    timeout = parse_float(request.args.get("timeout", 0.25), 0.25, 0.05, 2.0)

    try:
        registers = parse_registers(request.args.get("registers", "0,1"))
    except ValueError as exc:
        return json_error(str(exc), 400)

    try:
        result = scan_sensores_fisicos(
            port=port,
            baudrate=baudrate,
            start_id=start_id,
            end_id=end_id,
            registers=registers,
            function_code=function_code,
            timeout=timeout,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    except RuntimeError as exc:
        return json_error(str(exc), 500)
    except Exception:
        return json_error("Falha inesperada ao escanear sensores fisicos.", 500)

    return jsonify(result)


@main_bp.route("/api/medicoes", methods=["OPTIONS"])
@main_bp.route("/api/monitoramento", methods=["OPTIONS"])
@main_bp.route("/api/alertas", methods=["OPTIONS"])
@main_bp.route("/api/sensores/fisicos", methods=["OPTIONS"])
def medicoes_options():
    return ("", 204)