"""
Gerencia sessões ativas de medição em memória.

Cada sessão tem um TTL de SESSAO_TTL_SEGUNDOS. Se o app parar
de enviar heartbeats (ex: travou ou foi fechado), a sessão expira
automaticamente e o ambiente é liberado.
"""

import threading
from datetime import datetime, timedelta, timezone

SESSAO_TTL_SEGUNDOS = 60

# { sensor_id: { "device_id": str, "expires_at": datetime } }
_sessoes: dict[str, dict] = {}
_lock = threading.Lock()


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _limpar_expiradas() -> None:
    """Remove sessões cujo TTL já expirou."""
    agora = _agora()
    expiradas = [sid for sid, s in _sessoes.items() if s["expires_at"] <= agora]
    for sid in expiradas:
        del _sessoes[sid]


def ocupar_ambiente(sensor_id: str, device_id: str) -> dict:
    """
    Tenta reservar o ambiente para o device_id.

    Retorna {"ok": True} em caso de sucesso.
    Levanta RuntimeError se o ambiente já estiver ocupado por outro device.
    """
    with _lock:
        _limpar_expiradas()
        sessao = _sessoes.get(sensor_id)
        if sessao:
            if sessao["device_id"] != device_id:
                raise RuntimeError(f"Ambiente já está em uso por outro dispositivo.")
            # Mesmo device renovando — apenas atualiza TTL
        _sessoes[sensor_id] = {
            "device_id": device_id,
            "expires_at": _agora() + timedelta(seconds=SESSAO_TTL_SEGUNDOS),
        }
        return {"ok": True}


def liberar_ambiente(sensor_id: str, device_id: str) -> dict:
    """
    Libera o ambiente se ele pertencer ao device_id informado.

    Retorna {"ok": True} em caso de sucesso, {"ok": False} se não havia sessão
    ou se pertencia a outro device.
    """
    with _lock:
        sessao = _sessoes.get(sensor_id)
        if not sessao or sessao["device_id"] != device_id:
            return {"ok": False}
        del _sessoes[sensor_id]
        return {"ok": True}


def heartbeat_sessao(sensor_id: str, device_id: str) -> dict:
    """
    Renova o TTL da sessão ativa.

    Levanta RuntimeError se o ambiente não estiver reservado por este device.
    """
    with _lock:
        _limpar_expiradas()
        sessao = _sessoes.get(sensor_id)
        if not sessao or sessao["device_id"] != device_id:
            raise RuntimeError("Sessão não encontrada ou pertence a outro dispositivo.")
        sessao["expires_at"] = _agora() + timedelta(seconds=SESSAO_TTL_SEGUNDOS)
        return {"ok": True}


def esta_ocupado(sensor_id: str) -> bool:
    """Retorna True se o ambiente estiver com sessão ativa."""
    with _lock:
        _limpar_expiradas()
        return sensor_id in _sessoes


def listar_sessoes() -> list[dict]:
    """Retorna a lista de sessões ativas (para debug/admin)."""
    with _lock:
        _limpar_expiradas()
        return [
            {
                "sensor_id": sid,
                "device_id": s["device_id"],
                "expires_at": s["expires_at"].isoformat(),
            }
            for sid, s in _sessoes.items()
        ]
