import pytest

from app.services.monitoramento_service import scan_sensores_fisicos


def test_scan_sem_dependencias_serial(monkeypatch):
    monkeypatch.setattr("app.services.monitoramento_service.SERIAL_SCAN_AVAILABLE", False)
    with pytest.raises(RuntimeError):
        scan_sensores_fisicos(
            port="/dev/serial0",
            baudrate=9600,
            start_id=1,
            end_id=3,
            registers=[0, 1],
            function_code=3,
            timeout=0.25,
        )


def test_scan_validacoes(monkeypatch):
    monkeypatch.setattr("app.services.monitoramento_service.SERIAL_SCAN_AVAILABLE", True)

    with pytest.raises(ValueError):
        scan_sensores_fisicos(
            port="/dev/serial0",
            baudrate=9600,
            start_id=0,
            end_id=3,
            registers=[0],
            function_code=3,
            timeout=0.25,
        )

    with pytest.raises(ValueError):
        scan_sensores_fisicos(
            port="/dev/serial0",
            baudrate=9600,
            start_id=1,
            end_id=3,
            registers=[0],
            function_code=99,
            timeout=0.25,
        )

    with pytest.raises(ValueError):
        scan_sensores_fisicos(
            port="/dev/serial0",
            baudrate=9600,
            start_id=1,
            end_id=3,
            registers=[],
            function_code=3,
            timeout=0.25,
        )
