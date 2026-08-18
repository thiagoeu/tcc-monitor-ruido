def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "monitor-ruido-backend"
    assert "database" in data
    assert "timestamp" in data


def test_health_invalido_nao_existe(client):
    assert client.get("/health/foo").status_code == 404
