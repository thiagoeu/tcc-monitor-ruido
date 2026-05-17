from flask import jsonify, request

from app.services import (
    create_ambiente,
    delete_ambiente,
    list_ambientes,
    update_ambiente,
)

from . import main_bp


def json_error(message, status=400):
    response = jsonify({"erro": message})
    response.status_code = status
    return response


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


@main_bp.route("/api/ambientes", methods=["OPTIONS"])
@main_bp.route("/api/ambientes/<int:ambiente_id>", methods=["OPTIONS"])
def ambientes_options():
    return ("", 204)