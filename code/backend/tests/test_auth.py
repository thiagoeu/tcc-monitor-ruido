def test_login_admin_ok(client_raw):
    response = client_raw.post("/api/auth/login", json={
        "email": "admin@noiseradar.local",
        "senha": "admin123",
    })
    assert response.status_code == 200

    data = response.get_json()
    assert "token" in data
    assert "expira_em" in data
    assert data["usuario"]["email"] == "admin@noiseradar.local"
    assert data["usuario"]["papel"] == "admin"


def test_login_sem_campos(client_raw):
    for payload in ({}, {"email": "x@x.com"}, {"senha": "123"}):
        response = client_raw.post("/api/auth/login", json=payload)
        assert response.status_code == 400


def test_login_credenciais_invalidas(client_raw):
    response = client_raw.post("/api/auth/login", json={
        "email": "admin@noiseradar.local",
        "senha": "senha-errada",
    })
    assert response.status_code == 401

    response = client_raw.post("/api/auth/login", json={
        "email": "nao-existe@noiseradar.local",
        "senha": "admin123",
    })
    assert response.status_code == 401


def test_me_retorna_usuario(client_raw, auth_token):
    response = client_raw.get("/api/auth/me", headers={
        "Authorization": f"Bearer {auth_token}",
    })
    assert response.status_code == 200
    assert response.get_json()["email"] == "admin@noiseradar.local"


def test_me_sem_token(client_raw):
    assert client_raw.get("/api/auth/me").status_code == 401


def test_me_token_invalido(client_raw):
    response = client_raw.get("/api/auth/me", headers={
        "Authorization": "Bearer token-invalido",
    })
    assert response.status_code == 401


def test_logout_revoga_token(client_raw, auth_token):
    response = client_raw.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {auth_token}",
    })
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    response = client_raw.get("/api/auth/me", headers={
        "Authorization": f"Bearer {auth_token}",
    })
    assert response.status_code == 401


def test_logout_sem_token(client_raw):
    assert client_raw.post("/api/auth/logout").status_code == 200


def test_endpoint_protegido_sem_token(client_raw):
    for path in (
        "/api/monitoramento",
        "/api/alertas",
        "/api/relatorios/resumo",
        "/api/sessoes",
        "/api/sensores/fisicos",
    ):
        assert client_raw.get(path).status_code == 401

    assert client_raw.post("/api/ambientes", json={}).status_code == 401
    assert client_raw.put("/api/ambientes/1", json={}).status_code == 401
    assert client_raw.delete("/api/ambientes/1").status_code == 401


def test_ambientes_lista_continua_aberto(client_raw):
    response = client_raw.get("/api/ambientes")
    assert response.status_code == 200


def test_admin_cria_usuario(client, client_raw, auth_token):
    response = client.post("/api/usuarios", json={
        "nome": "Maria",
        "email": "maria@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    assert response.status_code == 201

    data = response.get_json()
    assert data["nome"] == "Maria"
    assert data["email"] == "maria@noiseradar.local"
    assert data["papel"] == "visualizador"
    assert "senha_hash" not in data
    assert "token" not in data

    usuarios = client.get("/api/usuarios").get_json()
    assert len(usuarios) == 2


def test_novo_usuario_faz_login(client, client_raw):
    client.post("/api/usuarios", json={
        "nome": "Joao",
        "email": "joao@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })

    response = client_raw.post("/api/auth/login", json={
        "email": "joao@noiseradar.local",
        "senha": "senha123",
    })
    assert response.status_code == 200
    assert response.get_json()["usuario"]["papel"] == "visualizador"


def test_cria_usuario_email_duplicado(client):
    response = client.post("/api/usuarios", json={
        "nome": "Outro",
        "email": "admin@noiseradar.local",
        "senha": "senha123",
    })
    assert response.status_code == 409


def test_cria_usuario_payload_invalido(client):
    for payload in (
        {},
        {"nome": "X", "email": "x@x.com"},
        {"nome": "X", "email": "x@x.com", "senha": "123", "papel": "deus"},
    ):
        response = client.post("/api/usuarios", json=payload)
        assert response.status_code == 400


def test_usuarios_requer_admin(client, client_raw, auth_token):
    client.post("/api/usuarios", json={
        "nome": "Leitor",
        "email": "leitor@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })

    login = client_raw.post("/api/auth/login", json={
        "email": "leitor@noiseradar.local",
        "senha": "senha123",
    })
    token = login.get_json()["token"]

    response = client_raw.get("/api/usuarios", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 403

    response = client_raw.post("/api/usuarios", json={
        "nome": "X",
        "email": "x@x.com",
        "senha": "123456",
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403