"""
test_usuarios_crud.py

Testa os novos endpoints de CRUD de usuários:
  GET    /api/usuarios/<id>
  PUT    /api/usuarios/<id>
  DELETE /api/usuarios/<id>
  PUT    /api/usuarios/<id>/senha
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

@pytest.fixture()
def visualizador(client, client_raw):
    """Cria um usuário visualizador e retorna (dados, token)."""
    resp = client.post("/api/usuarios", json={
        "nome": "Observador",
        "email": "obs@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    assert resp.status_code == 201
    dados = resp.get_json()

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "obs@noiseradar.local",
        "senha": "senha123",
    })
    assert login_resp.status_code == 200
    token = login_resp.get_json()["token"]
    return dados, token


# ---------------------------------------------------------------------------
# GET /api/usuarios/<id>
# ---------------------------------------------------------------------------

def test_admin_get_usuario_por_id(client):
    """Admin consegue ver detalhes de um usuário pelo ID."""
    resp = client.get("/api/usuarios/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["email"] == "admin@noiseradar.local"
    assert data["papel"] == "admin_master"
    assert "senha_hash" not in data
    assert "token" not in data


def test_get_usuario_inexistente(client):
    """Retorna 404 para usuário que não existe."""
    resp = client.get("/api/usuarios/9999")
    assert resp.status_code == 404


def test_visualizador_nao_acessa_get_usuario(client_raw, visualizador):
    """Visualizador recebe 403 ao tentar acessar detalhes de um usuário."""
    _, token = visualizador
    resp = client_raw.get("/api/usuarios/1", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/usuarios/<id>
# ---------------------------------------------------------------------------

def test_admin_update_usuario_nome(client):
    """Admin atualiza só o nome de um usuário."""
    resp = client.post("/api/usuarios", json={
        "nome": "Inicial",
        "email": "inicial@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}", json={"nome": "Atualizado"})
    assert resp.status_code == 200
    assert resp.get_json()["nome"] == "Atualizado"
    assert resp.get_json()["email"] == "inicial@noiseradar.local"


def test_admin_update_usuario_papel(client):
    """Admin promove visualizador a admin."""
    resp = client.post("/api/usuarios", json={
        "nome": "Promovido",
        "email": "promovido@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}", json={"papel": "admin"})
    assert resp.status_code == 200
    assert resp.get_json()["papel"] == "admin"


def test_admin_update_usuario_email_duplicado(client):
    """Retorna 409 ao tentar usar email já cadastrado."""
    client.post("/api/usuarios", json={
        "nome": "A",
        "email": "a@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    resp = client.post("/api/usuarios", json={
        "nome": "B",
        "email": "b@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid_b = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid_b}", json={"email": "a@noiseradar.local"})
    assert resp.status_code == 409


def test_admin_update_usuario_papel_invalido(client):
    """Retorna 400 para papel inválido."""
    resp = client.post("/api/usuarios", json={
        "nome": "C",
        "email": "c@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}", json={"papel": "superusuario"})
    assert resp.status_code == 400


def test_admin_update_usuario_nome_vazio(client):
    """Retorna 400 para nome vazio."""
    resp = client.post("/api/usuarios", json={
        "nome": "D",
        "email": "d@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}", json={"nome": "   "})
    assert resp.status_code == 400


def test_admin_update_usuario_inexistente(client):
    """Retorna 404 ao tentar editar usuário que não existe."""
    resp = client.put("/api/usuarios/9999", json={"nome": "X"})
    assert resp.status_code == 404


def test_visualizador_nao_acessa_put_usuario(client_raw, visualizador):
    """Visualizador recebe 403 ao tentar editar usuário."""
    _, token = visualizador
    resp = client_raw.put("/api/usuarios/1", json={"nome": "Hacker"}, headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 403


def test_update_sem_campos_retorna_usuario_inalterado(client):
    """PUT sem nenhum campo retorna o usuário sem alteração (200)."""
    resp = client.post("/api/usuarios", json={
        "nome": "Sem Mudanca",
        "email": "semudanca@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}", json={})
    assert resp.status_code == 200
    assert resp.get_json()["nome"] == "Sem Mudanca"


# ---------------------------------------------------------------------------
# DELETE /api/usuarios/<id>
# ---------------------------------------------------------------------------

def test_admin_desativa_usuario(client, client_raw):
    """Admin desativa usuário; login subsequente falha com 401."""
    resp = client.post("/api/usuarios", json={
        "nome": "Desativado",
        "email": "desativado@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.delete(f"/api/usuarios/{uid}")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "desativado@noiseradar.local",
        "senha": "senha123",
    })
    assert login_resp.status_code == 401

    # Dados ainda existem no banco (soft-delete) - ativo=0
    detail = client.get(f"/api/usuarios/{uid}")
    assert detail.status_code == 200
    assert detail.get_json()["ativo"] == 0


def test_admin_nao_pode_desativar_si_mesmo(client):
    """Admin recebe 400 ao tentar desativar a própria conta."""
    resp = client.delete("/api/usuarios/1")
    assert resp.status_code == 400
    assert "própria conta" in resp.get_json()["erro"]


def test_delete_usuario_inexistente(client):
    """Retorna 404 para usuário que não existe."""
    resp = client.delete("/api/usuarios/9999")
    assert resp.status_code == 404


def test_delete_usuario_ja_inativo(client):
    """Retorna 404 ao tentar desativar usuário já inativo."""
    resp = client.post("/api/usuarios", json={
        "nome": "JaInativo",
        "email": "jainativo@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    client.delete(f"/api/usuarios/{uid}")       # primeira vez: 200
    resp = client.delete(f"/api/usuarios/{uid}")  # segunda vez: 404
    assert resp.status_code == 404


def test_visualizador_nao_acessa_delete(client_raw, visualizador):
    """Visualizador recebe 403 ao tentar deletar usuário."""
    _, token = visualizador
    resp = client_raw.delete("/api/usuarios/1", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/usuarios/<id>/senha
# ---------------------------------------------------------------------------

def test_admin_troca_senha_sem_senha_atual(client, client_raw):
    """Admin troca senha de outro usuário sem informar a senha atual."""
    resp = client.post("/api/usuarios", json={
        "nome": "SenhaTroca",
        "email": "senhatroca@noiseradar.local",
        "senha": "senhavelha",
        "papel": "visualizador",
    })
    uid = resp.get_json()["id"]

    resp = client.put(f"/api/usuarios/{uid}/senha", json={
        "nova_senha": "novaSenha99",
    })
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "senhatroca@noiseradar.local",
        "senha": "novaSenha99",
    })
    assert login_resp.status_code == 200

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "senhatroca@noiseradar.local",
        "senha": "senhavelha",
    })
    assert login_resp.status_code == 401


def test_usuario_troca_propria_senha(client_raw, visualizador):
    """Usuário troca a própria senha informando a senha atual."""
    dados, token = visualizador
    uid = dados["id"]

    resp = client_raw.put(f"/api/usuarios/{uid}/senha", json={
        "senha_atual": "senha123",
        "nova_senha": "novaSenha456",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    login_resp = client_raw.post("/api/auth/login", json={
        "email": "obs@noiseradar.local",
        "senha": "novaSenha456",
    })
    assert login_resp.status_code == 200


def test_usuario_senha_atual_errada(client_raw, visualizador):
    """Retorna 401 se a senha atual informada estiver incorreta."""
    dados, token = visualizador
    uid = dados["id"]

    resp = client_raw.put(f"/api/usuarios/{uid}/senha", json={
        "senha_atual": "senhaERRADA",
        "nova_senha": "novaSenha456",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_usuario_nao_troca_senha_de_outro(client_raw, visualizador):
    """Visualizador recebe 403 ao tentar trocar senha de outro usuário."""
    _, token = visualizador

    resp = client_raw.put("/api/usuarios/1/senha", json={
        "senha_atual": "qualquer",
        "nova_senha": "novaSenha456",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_change_senha_nova_muito_curta(client):
    """Retorna 400 se nova_senha tiver menos de 6 caracteres."""
    resp = client.put("/api/usuarios/1/senha", json={
        "nova_senha": "123",
    })
    assert resp.status_code == 400


def test_change_senha_sem_nova_senha(client):
    """Retorna 400 se nova_senha não for fornecida."""
    resp = client.put("/api/usuarios/1/senha", json={})
    assert resp.status_code == 400


def test_change_senha_usuario_inexistente(client):
    """Retorna 404 para usuário que não existe."""
    resp = client.put("/api/usuarios/9999/senha", json={
        "nova_senha": "novaSenha99",
    })
    assert resp.status_code == 404


def test_change_senha_sem_senha_atual_nao_admin(client_raw, visualizador):
    """Visualizador recebe 400 ao omitir senha_atual ao trocar a própria senha."""
    dados, token = visualizador
    uid = dados["id"]

    resp = client_raw.put(f"/api/usuarios/{uid}/senha", json={
        "nova_senha": "novaSenha456",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

# ---------------------------------------------------------------------------
# Testes de RBAC com três papéis
# ---------------------------------------------------------------------------

@pytest.fixture()
def visualizador_criado(client):
    """Cria um visualizador e retorna seus dados."""
    resp = client.post("/api/usuarios", json={
        "nome": "Vis Teste",
        "email": "vis.teste@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    assert resp.status_code == 201
    return resp.get_json()


# ── admin_master pode criar admin ──────────────────────────────────────────

def test_admin_master_cria_admin(client):
    """admin_master pode criar usuário com papel 'admin'."""
    resp = client.post("/api/usuarios", json={
        "nome": "Novo Admin",
        "email": "novoadmin@noiseradar.local",
        "senha": "senha123",
        "papel": "admin",
    })
    assert resp.status_code == 201
    assert resp.get_json()["papel"] == "admin"


# ── admin normal cria visualizador ────────────────────────────────────────

def test_admin_normal_cria_visualizador(admin_normal_client):
    """admin pode criar usuário visualizador."""
    resp = admin_normal_client.post("/api/usuarios", json={
        "nome": "Vis OK",
        "email": "visok@noiseradar.local",
        "senha": "senha123",
        "papel": "visualizador",
    })
    assert resp.status_code == 201


def test_admin_normal_nao_cria_admin(admin_normal_client):
    """admin NÃO pode criar usuário com papel 'admin'."""
    resp = admin_normal_client.post("/api/usuarios", json={
        "nome": "Hack Admin",
        "email": "hackadmin@noiseradar.local",
        "senha": "senha123",
        "papel": "admin",
    })
    assert resp.status_code == 403


def test_admin_normal_nao_cria_admin_master(admin_normal_client):
    """admin NÃO pode criar usuário com papel 'admin_master'."""
    resp = admin_normal_client.post("/api/usuarios", json={
        "nome": "Hack Master",
        "email": "hackmaster@noiseradar.local",
        "senha": "senha123",
        "papel": "admin_master",
    })
    assert resp.status_code == 403


# ── admin normal edita visualizador ──────────────────────────────────────

def test_admin_normal_edita_visualizador(admin_normal_client, visualizador_criado):
    """admin pode editar um visualizador."""
    uid = visualizador_criado["id"]
    resp = admin_normal_client.put(f"/api/usuarios/{uid}", json={"nome": "Vis Editado"})
    assert resp.status_code == 200
    assert resp.get_json()["nome"] == "Vis Editado"


def test_admin_normal_nao_edita_admin(client, admin_normal_client):
    """admin NÃO pode editar outro admin."""
    resp = client.post("/api/usuarios", json={
        "nome": "Segundo Admin",
        "email": "seg_admin@noiseradar.local",
        "senha": "senha123",
        "papel": "admin",
    })
    uid = resp.get_json()["id"]
    resp = admin_normal_client.put(f"/api/usuarios/{uid}", json={"nome": "Hack"})
    assert resp.status_code == 403


def test_admin_normal_nao_pode_promover_para_admin(admin_normal_client, visualizador_criado):
    """admin NÃO pode promover visualizador a admin."""
    uid = visualizador_criado["id"]
    resp = admin_normal_client.put(f"/api/usuarios/{uid}", json={"papel": "admin"})
    assert resp.status_code == 403


# ── admin normal desativa visualizador ──────────────────────────────────

def test_admin_normal_desativa_visualizador(admin_normal_client, visualizador_criado):
    """admin pode desativar um visualizador."""
    uid = visualizador_criado["id"]
    resp = admin_normal_client.delete(f"/api/usuarios/{uid}")
    assert resp.status_code == 200


def test_admin_normal_nao_desativa_admin(client, admin_normal_client):
    """admin NÃO pode desativar outro admin."""
    resp = client.post("/api/usuarios", json={
        "nome": "Admin2",
        "email": "admin2@noiseradar.local",
        "senha": "senha123",
        "papel": "admin",
    })
    uid = resp.get_json()["id"]
    resp = admin_normal_client.delete(f"/api/usuarios/{uid}")
    assert resp.status_code == 403


# ── admin normal troca senha de visualizador ─────────────────────────────

def test_admin_normal_troca_senha_visualizador(admin_normal_client, visualizador_criado):
    """admin pode trocar senha de visualizador sem informar a atual."""
    uid = visualizador_criado["id"]
    resp = admin_normal_client.put(f"/api/usuarios/{uid}/senha", json={"nova_senha": "novaSenha99"})
    assert resp.status_code == 200


def test_admin_normal_nao_troca_senha_de_admin(client, admin_normal_client):
    """admin NÃO pode trocar senha de outro admin."""
    resp = client.post("/api/usuarios", json={
        "nome": "Admin Senha",
        "email": "adminsenha@noiseradar.local",
        "senha": "senha123",
        "papel": "admin",
    })
    uid = resp.get_json()["id"]
    resp = admin_normal_client.put(f"/api/usuarios/{uid}/senha", json={"nova_senha": "novaSenha99"})
    assert resp.status_code == 403
