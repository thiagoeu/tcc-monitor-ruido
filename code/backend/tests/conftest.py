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
def client_raw(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def limpar_sessoes():
    from app.services import sessoes_service

    sessoes_service._sessoes.clear()
    yield
    sessoes_service._sessoes.clear()


class _AuthedClient:
    """Wrapper que injeta o header Authorization do token em toda chamada."""

    def __init__(self, client, token):
        self._client = client
        self._headers = {"Authorization": f"Bearer {token}"}

    def _kwargs(self, kwargs):
        kwargs = dict(kwargs)
        headers = dict(self._headers)
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        return kwargs

    def get(self, *args, **kwargs):
        return self._client.get(*args, **self._kwargs(kwargs))

    def post(self, *args, **kwargs):
        return self._client.post(*args, **self._kwargs(kwargs))

    def put(self, *args, **kwargs):
        return self._client.put(*args, **self._kwargs(kwargs))

    def delete(self, *args, **kwargs):
        return self._client.delete(*args, **self._kwargs(kwargs))

    def patch(self, *args, **kwargs):
        return self._client.patch(*args, **self._kwargs(kwargs))


@pytest.fixture()
def auth_token(client_raw):
    response = client_raw.post("/api/auth/login", json={
        "email": "admin@noiseradar.local",
        "senha": "admin123",
    })
    assert response.status_code == 200
    return response.get_json()["token"]


@pytest.fixture()
def client(client_raw, auth_token):
    """Client autenticado como admin (token injetado automaticamente)."""
    return _AuthedClient(client_raw, auth_token)


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


@pytest.fixture()
def admin_normal_client(client, client_raw):
    """Cria um admin (não master) e retorna um _AuthedClient autenticado como ele."""
    resp = client.post("/api/usuarios", json={
        "nome": "Admin Normal",
        "email": "adminormal@noiseradar.local",
        "senha": "admin456",
        "papel": "admin",
    })
    assert resp.status_code == 201, resp.get_json()

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "adminormal@noiseradar.local",
        "senha": "admin456",
    })
    assert login_resp.status_code == 200
    token = login_resp.get_json()["token"]
    return _AuthedClient(client_raw, token)