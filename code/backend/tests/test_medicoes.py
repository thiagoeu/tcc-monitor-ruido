def test_cria_medicao_dentro_do_limite(client, ambiente):
    response = client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 55.5,
    })
    assert response.status_code == 200

    data = response.get_json()
    assert data["ok"] is True
    assert data["sensor_id"] == ambiente["sensor_id"]
    assert data["db"] == 55.5
    assert data["excedeu_limite"] is False
    assert data["alerta_criado"] is False
    assert "timestamp" in data


def test_cria_medicao_acima_do_limite_gera_alerta(client, ambiente):
    response = client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 90.0,
    })
    assert response.status_code == 200

    data = response.get_json()
    assert data["excedeu_limite"] is True
    assert data["alerta_criado"] is True

    alertas = client.get("/api/alertas").get_json()
    assert len(alertas) == 1
    assert alertas[0]["ambiente_id"] == ambiente["id"]
    assert "Ruído acima do limite" in alertas[0]["mensagem"]


def test_cria_medicao_sensor_desconhecido(client):
    response = client.post("/api/medicoes", json={
        "sensor_id": "sensor-inexistente",
        "db": 50,
    })
    assert response.status_code == 404


def test_cria_medicao_ambiente_inativo(client, ambiente):
    client.put(f"/api/ambientes/{ambiente['id']}", json={"ativo": False})

    response = client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 50,
    })
    assert response.status_code == 404


def test_cria_medicao_sem_sensor_id(client):
    response = client.post("/api/medicoes", json={"db": 50})
    assert response.status_code == 400


def test_cria_medicao_db_invalido(client, ambiente):
    response = client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": "alto",
    })
    assert response.status_code == 400


def test_monitoramento_retorna_estrutura(client, ambiente):
    client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 70,
    })

    response = client.get("/api/monitoramento")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data["ambientes"]) == 1
    assert len(data["medicoes"]) == 1
    assert len(data["alertas"]) == 1
    assert "ultima_por_ambiente" in data
    assert "servidor_em" in data
    assert str(ambiente["id"]) in data["ultima_por_ambiente"]


def test_monitoramento_limita_medicoes(client, ambiente):
    for _ in range(5):
        client.post("/api/medicoes", json={
            "sensor_id": ambiente["sensor_id"],
            "db": 50,
        })

    response = client.get("/api/monitoramento?limit=2")
    assert response.status_code == 200
    assert len(response.get_json()["medicoes"]) == 2


def test_monitoramento_limit_invalido_usa_default(client, ambiente):
    client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 50,
    })

    response = client.get("/api/monitoramento?limit=abc")
    assert response.status_code == 200
    assert len(response.get_json()["medicoes"]) == 1


def test_alertas_limite(client, ambiente):
    for _ in range(3):
        client.post("/api/medicoes", json={
            "sensor_id": ambiente["sensor_id"],
            "db": 90,
        })

    assert len(client.get("/api/alertas?limit=2").get_json()) == 2
    assert len(client.get("/api/alertas").get_json()) == 3
