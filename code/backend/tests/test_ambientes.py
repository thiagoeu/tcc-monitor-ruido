def test_lista_ambientes_vazio(client):
    response = client.get("/api/ambientes")
    assert response.status_code == 200
    assert response.get_json() == []


def test_cria_ambiente(client):
    response = client.post("/api/ambientes", json={
        "nome": "Biblioteca",
        "localizacao": "Bloco B",
        "sensor_id": "sensor-001",
        "limite_db": 60,
    })
    assert response.status_code == 201

    data = response.get_json()
    assert data["nome"] == "Biblioteca"
    assert data["localizacao"] == "Bloco B"
    assert data["sensor_id"] == "sensor-001"
    assert data["limite_db"] == 60
    assert data["ativo"] == 1
    assert data["id"] > 0
    assert "created_at" in data


def test_cria_ambiente_usa_limite_padrao(client):
    response = client.post("/api/ambientes", json={
        "nome": "Sala",
        "localizacao": "Bloco C",
        "sensor_id": "sensor-002",
    })
    assert response.status_code == 201
    assert response.get_json()["limite_db"] == 65


def test_cria_ambiente_sem_campos_obrigatorios(client):
    for payload in ({}, {"nome": "X"}, {"nome": "X", "localizacao": "Y"}):
        response = client.post("/api/ambientes", json=payload)
        assert response.status_code == 400
        assert "erro" in response.get_json()


def test_cria_ambiente_sensor_duplicado(client, ambiente):
    response = client.post("/api/ambientes", json={
        "nome": "Outro",
        "localizacao": "Bloco D",
        "sensor_id": ambiente["sensor_id"],
    })
    assert response.status_code == 409


def test_cria_ambiente_limite_invalido(client):
    response = client.post("/api/ambientes", json={
        "nome": "Sala",
        "localizacao": "Bloco E",
        "sensor_id": "sensor-003",
        "limite_db": "muito-alto",
    })
    assert response.status_code == 400

    response = client.post("/api/ambientes", json={
        "nome": "Sala",
        "localizacao": "Bloco E",
        "sensor_id": "sensor-003",
        "limite_db": -5,
    })
    assert response.status_code == 400


def test_lista_ambientes_com_filtro_ativo(client, ambiente):
    client.post("/api/ambientes", json={
        "nome": "Inativo",
        "localizacao": "Bloco F",
        "sensor_id": "sensor-004",
        "limite_db": 70,
    })
    todos = client.get("/api/ambientes").get_json()
    assert len(todos) == 2

    ativos = client.get("/api/ambientes?ativo=1").get_json()
    assert len(ativos) == 2

    client.put(f"/api/ambientes/{todos[1]['id']}", json={"ativo": False})
    ativos = client.get("/api/ambientes?ativo=1").get_json()
    assert len(ativos) == 1


def test_atualiza_ambiente(client, ambiente):
    response = client.put(f"/api/ambientes/{ambiente['id']}", json={
        "nome": "Laboratorio 2",
        "limite_db": 55,
    })
    assert response.status_code == 200

    data = response.get_json()
    assert data["nome"] == "Laboratorio 2"
    assert data["limite_db"] == 55
    assert data["sensor_id"] == ambiente["sensor_id"]


def test_atualiza_ambiente_nao_encontrado(client):
    response = client.put("/api/ambientes/9999", json={"nome": "X"})
    assert response.status_code == 404


def test_atualiza_ambiente_nome_vazio(client, ambiente):
    response = client.put(f"/api/ambientes/{ambiente['id']}", json={"nome": "  "})
    assert response.status_code == 400


def test_atualiza_ambiente_sensor_duplicado(client, ambiente):
    client.post("/api/ambientes", json={
        "nome": "Outro",
        "localizacao": "Bloco G",
        "sensor_id": "sensor-outro",
    })
    response = client.put(f"/api/ambientes/{ambiente['id']}", json={
        "sensor_id": "sensor-outro",
    })
    assert response.status_code == 409


def test_deleta_ambiente(client, ambiente):
    response = client.delete(f"/api/ambientes/{ambiente['id']}")
    assert response.status_code == 200

    data = response.get_json()
    assert data["ok"] is True
    assert data["ambiente"]["id"] == ambiente["id"]

    assert client.get("/api/ambientes").get_json() == []


def test_deleta_ambiente_nao_encontrado(client):
    response = client.delete("/api/ambientes/9999")
    assert response.status_code == 404
