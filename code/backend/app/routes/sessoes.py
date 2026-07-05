from flask import jsonify, request

from app.services import ocupar_ambiente, liberar_ambiente, heartbeat_sessao, listar_sessoes

from . import main_bp


def json_error(message, status=400):
    response = jsonify({"erro": message})
    response.status_code = status
    return response


@main_bp.route("/api/sessoes", methods=["GET"])
def http_listar_sessoes():
    """Lista todas as sessões ativas (útil para debug/admin)."""
    return jsonify(listar_sessoes())


@main_bp.route("/api/sessoes", methods=["POST"])
def http_ocupar_ambiente():
    """
    Reserva um ambiente para um dispositivo.

    Body: { "sensor_id": str, "device_id": str }
    Retorna 200 se ocupado com sucesso, 409 se já ocupado por outro.
    """
    payload = request.get_json(silent=True) or {}
    sensor_id = str(payload.get("sensor_id", "")).strip()
    device_id = str(payload.get("device_id", "")).strip()

    if not sensor_id or not device_id:
        return json_error("Campos obrigatórios: sensor_id e device_id.", 400)

    try:
        result = ocupar_ambiente(sensor_id, device_id)
    except RuntimeError as exc:
        return json_error(str(exc), 409)

    return jsonify(result)


@main_bp.route("/api/sessoes/<sensor_id>", methods=["DELETE"])
def http_liberar_ambiente(sensor_id):
    """
    Libera o ambiente reservado pelo dispositivo.

    Body: { "device_id": str }
    """
    payload = request.get_json(silent=True) or {}
    device_id = str(payload.get("device_id", "")).strip()

    if not device_id:
        return json_error("Campo obrigatório: device_id.", 400)

    result = liberar_ambiente(sensor_id, device_id)
    return jsonify(result)


@main_bp.route("/api/sessoes/<sensor_id>/heartbeat", methods=["PUT"])
def http_heartbeat_sessao(sensor_id):
    """
    Renova o TTL da sessão ativa.

    Body: { "device_id": str }
    """
    payload = request.get_json(silent=True) or {}
    device_id = str(payload.get("device_id", "")).strip()

    if not device_id:
        return json_error("Campo obrigatório: device_id.", 400)

    try:
        result = heartbeat_sessao(sensor_id, device_id)
    except RuntimeError as exc:
        return json_error(str(exc), 404)

    return jsonify(result)


@main_bp.route("/api/sessoes", methods=["OPTIONS"])
@main_bp.route("/api/sessoes/<sensor_id>", methods=["OPTIONS"])
@main_bp.route("/api/sessoes/<sensor_id>/heartbeat", methods=["OPTIONS"])
def sessoes_options(sensor_id=None):
    return ("", 204)
