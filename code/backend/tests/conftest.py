import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(config_overrides={
        "DB_PATH": str(db_path),
        "TESTING": True,
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def limpar_sessoes():
    from app.services import sessoes_service

    sessoes_service._sessoes.clear()
    yield
    sessoes_service._sessoes.clear()


@pytest.fixture()
def ambiente(client):
    response = client.post("/api/ambientes", json={
        "nome": "Laboratorio",
        "localizacao": "Bloco A",
        "sensor_id": "sensor-teste-1",
        "limite_db": 65,
    })
    assert response.status_code == 201
    return response.get_json()
