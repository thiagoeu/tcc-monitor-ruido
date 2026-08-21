import app.services.sessoes_service as sessoes_service


def test_ocupar_ambiente(client, ambiente):
    response = client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_ocupar_ambiente_sem_campos(client):
    for payload in ({}, {"sensor_id": "x"}, {"device_id": "y"}):
        response = client.post("/api/sessoes", json=payload)
        assert response.status_code == 400


def test_ocupar_ambiente_ja_ocupado(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-2",
    })
    assert response.status_code == 409


def test_ocupar_ambiente_mesmo_device_renova(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    assert response.status_code == 200


def test_heartbeat_sessao(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.put(
        f"/api/sessoes/{ambiente['sensor_id']}/heartbeat",
        json={"device_id": "device-1"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_heartbeat_sem_device_id(client, ambiente):
    response = client.put(
        f"/api/sessoes/{ambiente['sensor_id']}/heartbeat",
        json={},
    )
    assert response.status_code == 400


def test_heartbeat_sessao_nao_encontrada(client, ambiente):
    response = client.put(
        f"/api/sessoes/{ambiente['sensor_id']}/heartbeat",
        json={"device_id": "device-outro"},
    )
    assert response.status_code == 404


def test_liberar_ambiente(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.delete(
        f"/api/sessoes/{ambiente['sensor_id']}",
        json={"device_id": "device-1"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_liberar_ambiente_sem_device_id(client, ambiente):
    response = client.delete(f"/api/sessoes/{ambiente['sensor_id']}", json={})
    assert response.status_code == 400


def test_liberar_ambiente_device_errado(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.delete(
        f"/api/sessoes/{ambiente['sensor_id']}",
        json={"device_id": "device-2"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"ok": False}


def test_listar_sessoes(client, ambiente):
    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    response = client.get("/api/sessoes")
    assert response.status_code == 200

    sessoes = response.get_json()
    assert len(sessoes) == 1
    assert sessoes[0]["sensor_id"] == ambiente["sensor_id"]
    assert sessoes[0]["device_id"] == "device-1"


def test_ambiente_fica_em_uso(client, ambiente):
    assert client.get("/api/ambientes").get_json()[0]["em_uso"] is False

    client.post("/api/sessoes", json={
        "sensor_id": ambiente["sensor_id"],
        "device_id": "device-1",
    })
    assert client.get("/api/ambientes").get_json()[0]["em_uso"] is True


def test_sessao_expirada_libera_ambiente(client, ambiente):
    sessao = {
        "device_id": "device-1",
        "expires_at": sessoes_service._agora(),
    }
    sessoes_service._sessoes[ambiente["sensor_id"]] = sessao

    assert sessoes_service.esta_ocupado(ambiente["sensor_id"]) is False
    assert ambiente["sensor_id"] not in sessoes_service._sessoes
