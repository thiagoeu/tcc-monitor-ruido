def test_resumo_sem_dados(client):
    response = client.get("/api/relatorios/resumo")
    assert response.status_code == 200

    data = response.get_json()
    assert data["janela_horas"] == 24
    assert data["geral"]["total_medicoes"] == 0
    assert data["geral"]["total_alertas"] == 0
    assert data["geral"]["percentual_alerta"] == 0.0
    assert data["ambientes"] == []


def test_resumo_com_medicoes(client, ambiente):
    client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 50,
    })
    client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 90,
    })

    response = client.get("/api/relatorios/resumo?hours=24")
    data = response.get_json()

    assert data["geral"]["total_medicoes"] == 2
    assert data["geral"]["total_alertas"] == 1
    assert data["geral"]["percentual_alerta"] == 50.0
    assert data["geral"]["media_db"] == 70.0
    assert data["geral"]["pico_db"] == 90.0
    assert data["geral"]["minimo_db"] == 50.0

    assert len(data["ambientes"]) == 1
    ambiente_resumo = data["ambientes"][0]
    assert ambiente_resumo["total_medicoes"] == 2
    assert ambiente_resumo["total_alertas"] == 1


def test_resumo_horas_invalidas_usa_default(client):
    response = client.get("/api/relatorios/resumo?hours=abc")
    assert response.status_code == 200
    assert response.get_json()["janela_horas"] == 24


def test_resumo_horas_limites(client):
    response = client.get("/api/relatorios/resumo?hours=999999")
    assert response.status_code == 200
    assert response.get_json()["janela_horas"] == 24 * 30

    response = client.get("/api/relatorios/resumo?hours=0")
    assert response.status_code == 200
    assert response.get_json()["janela_horas"] == 1


def test_relatorio_txt(client, ambiente):
    client.post("/api/medicoes", json={
        "sensor_id": ambiente["sensor_id"],
        "db": 70,
    })

    response = client.get("/api/relatorios/txt")
    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")

    content = response.get_data(as_text=True)
    assert "Relatório de Monitoramento de Ruído" in content
    assert "Resumo Geral" in content
    assert "Laboratorio" in content
    assert "Total de medições: 1" in content
    assert "Total de alertas: 1" in content
    assert "Content-Disposition" in response.headers
