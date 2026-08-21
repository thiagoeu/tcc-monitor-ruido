# Backend — NoiseRadar

Documentação do backend Flask + SQLite do sistema de monitoramento de ruído.

> Para o sistema de login em detalhes (credenciais, seed, tokens), veja [AUTH.md](./AUTH.md).

---

## Arquitetura

Padrão em camadas:

```text
backend/
┣ app/
┃ ┣ routes/          # Camada HTTP (blueprints) — parse, validação de request, JSON
┃ ┃ ┣ __init__.py    # Cria o main_bp e registra todos os módulos de rotas
┃ ┃ ┣ health.py
┃ ┃ ┣ ambientes.py
┃ ┃ ┣ medicoes.py
┃ ┃ ┣ relatorios.py
┃ ┃ ┣ sessoes.py
┃ ┃ ┗ auth.py        # Decoradores login_required / admin_required + rotas de auth
┃ ┣ services/        # Regras de negócio — acesso ao banco, lógica
┃ ┃ ┣ ambientes_service.py
┃ ┃ ┣ medicoes_service.py
┃ ┃ ┣ monitoramento_service.py
┃ ┃ ┣ relatorios_service.py
┃ ┃ ┣ sessoes_service.py   # Sessões de medição em memória (TTL)
┃ ┃ ┗ auth_service.py      # Login/logout/usuários, hash e tokens
┃ ┣ database.py      # Conexão, schema (init_db) e seeds
┃ ┗ __init__.py      # create_app() — fábrica do app
┣ main.py            # Entry point (APP_HOST / APP_PORT / APP_DEBUG)
┣ requirements.txt
┣ requirements-dev.txt
┗ tests/             # Testes pytest
```

Regra simples: **`routes` não tocam no banco**; **`services` não montam resposta HTTP**.

---

## Banco de Dados (SQLite)

Arquivo: `backend/ruido.db` (criado automaticamente). Configurável via `DB_PATH`.

As tabelas são criadas com `CREATE TABLE IF NOT EXISTS` na inicialização — **não há migração manual**.

### Tabelas

**ambientes**

| Coluna        | Tipo    | Notas                              |
| ------------- | ------- | ---------------------------------- |
| id            | INTEGER | PK AUTOINCREMENT                   |
| nome          | TEXT    |                                    |
| localizacao   | TEXT    |                                    |
| sensor_id     | TEXT    | UNIQUE                             |
| limite_db     | REAL    | default 65                         |
| ativo         | INTEGER | 0/1, default 1                     |
| created_at    | TEXT    | ISO 8601 UTC                       |

**medicoes**

| Coluna        | Tipo    | Notas                              |
| ------------- | ------- | ---------------------------------- |
| id            | INTEGER | PK AUTOINCREMENT                   |
| ambiente_id   | INTEGER | FK → ambientes.id                  |
| db            | REAL    |                                    |
| excedeu_limite| INTEGER | 0/1                                |
| created_at    | TEXT    | ISO 8601 UTC                       |

**alertas**

| Coluna        | Tipo    | Notas                              |
| ------------- | ------- | ---------------------------------- |
| id            | INTEGER | PK AUTOINCREMENT                   |
| ambiente_id   | INTEGER | FK → ambientes.id                  |
| medicao_id    | INTEGER | FK → medicoes.id                   |
| mensagem      | TEXT    |                                    |
| created_at    | TEXT    | ISO 8601 UTC                       |

**usuarios** (login — detalhes em [AUTH.md](./AUTH.md))

| Coluna         | Tipo    | Notas                                     |
| -------------- | ------- | ----------------------------------------- |
| id             | INTEGER | PK AUTOINCREMENT                          |
| nome           | TEXT    |                                           |
| email          | TEXT    | UNIQUE                                    |
| senha_hash     | TEXT    | hash `werkzeug.security` (nunca texto puro)|
| papel          | TEXT    | `admin` \| `visualizador`, default `visualizador` |
| ativo          | INTEGER | 0/1, default 1                            |
| token          | TEXT    | token Bearer ativo (NULL = sem sessão)    |
| token_expira   | TEXT    | ISO 8601 UTC                              |
| created_at     | TEXT    | ISO 8601 UTC                              |
| last_login_at  | TEXT    | ISO 8601 UTC                              |

### Seeds automáticos

| Seed                     | Quando                                    | Como configurar        |
| ------------------------ | ----------------------------------------- | ---------------------- |
| Ambientes padrão         | `seed_default_environments()`             | hardcoded (e06a-001/002) |
| Admin inicial            | `seed_default_admin()` (se email não existe) | `ADMIN_EMAIL`, `ADMIN_SENHA`, `ADMIN_NOME` |

---

## Rotas da API

Legenda: 🔓 aberta · 🔐 exige `Authorization: Bearer <token>` · 👑 exige token de **admin**

### Saúde

| Método | Rota      | Proteção | Descrição        |
| ------ | --------- | -------- | ---------------- |
| GET    | `/health` | 🔓       | Health check     |

### Autenticação e Usuários

| Método | Rota                 | Proteção | Descrição                           |
| ------ | -------------------- | -------- | ----------------------------------- |
| POST   | `/api/auth/login`    | 🔓       | `{email, senha}` → `{token, expira_em, usuario}` |
| POST   | `/api/auth/logout`   | 🔓       | Revoga o token enviado              |
| GET    | `/api/auth/me`       | 🔐       | Usuário autenticado                 |
| GET    | `/api/usuarios`      | 👑       | Lista usuários                      |
| POST   | `/api/usuarios`      | 👑       | Cria usuário `{nome, email, senha, papel}` |

### Ambientes

| Método | Rota                              | Proteção | Descrição                  |
| ------ | --------------------------------- | -------- | -------------------------- |
| GET    | `/api/ambientes`                  | 🔓       | Lista (filtro `?ativo=1`)  |
| POST   | `/api/ambientes`                  | 🔐       | Cria ambiente              |
| PUT    | `/api/ambientes/<id>`             | 🔐       | Atualiza                   |
| DELETE | `/api/ambientes/<id>`             | 🔐       | Exclui (cascata em medições/alertas) |

> `GET /api/ambientes` permanece aberto porque o app mobile e os sensores dependem dele.

### Medições, Monitoramento e Alertas

| Método | Rota                       | Proteção | Descrição                             |
| ------ | -------------------------- | -------- | ------------------------------------- |
| POST   | `/api/medicoes`            | 🔓       | Registra medição `{sensor_id, db}`    |
| GET    | `/api/monitoramento`       | 🔐       | Dashboard (`?limit=`, default 60)     |
| GET    | `/api/alertas`             | 🔐       | Alertas recentes (`?limit=`, default 50) |
| GET    | `/api/sensores/fisicos`    | 🔐       | Scan Modbus (UART/serial)             |

### Relatórios

| Método | Rota                          | Proteção | Descrição                 |
| ------ | ----------------------------- | -------- | ------------------------- |
| GET    | `/api/relatorios/resumo`      | 🔐       | Resumo estatístico por janela (`?hours=`, default 24) |
| GET    | `/api/relatorios/txt`         | 🔐       | Download de relatório em texto plano |
| GET    | `/api/relatorios/csv`         | 🔐       | Download de relatório em CSV tabular |
| GET    | `/api/relatorios/pdf`         | 🔐       | Download de relatório em PDF com gráficos |

### Sessões de Medição (em memória, TTL 60s)

| Método | Rota                                  | Proteção | Descrição            |
| ------ | ------------------------------------- | -------- | -------------------- |
| GET    | `/api/sessoes`                        | 🔐       | Lista sessões ativas |
| POST   | `/api/sessoes`                        | 🔓       | Ocupa ambiente `{sensor_id, device_id}` |
| PUT    | `/api/sessoes/<sensor_id>/heartbeat`  | 🔓       | Renova TTL           |
| DELETE | `/api/sessoes/<sensor_id>`            | 🔓       | Libera ambiente      |

---

## Configuração (variáveis de ambiente)

| Variável               | Default                  | Descrição                          |
| ---------------------- | ------------------------ | ---------------------------------- |
| `APP_HOST`             | `0.0.0.0`                | Host do servidor                   |
| `APP_PORT`             | `5000`                   | Porta                              |
| `APP_DEBUG`            | `0`                      | `1` para debug (reload automático) |
| `APP_TOKEN_TTL_HORAS`  | `168` (7 dias)           | Validade do token Bearer           |
| `ADMIN_EMAIL`          | `admin@noiseradar.local` | E-mail do admin seed               |
| `ADMIN_SENHA`          | `admin123`               | Senha do admin seed ⚠️ troque em prod |
| `ADMIN_NOME`           | `Administrador`          | Nome do admin seed                 |
| `DB_PATH`              | `backend/ruido.db`       | Caminho do banco (via create_app)  |

> Nota: O admin seed é criado com o papel `admin_master`, que concede acesso total e capacidade de gerenciar todos os outros usuários, incluindo `admin`s comuns.

---

## Convenções de código

### Respostas de erro

Todos os módulos usam um helper `json_error(message, status)`:

```python
def json_error(message, status=400):
    response = jsonify({"erro": message})
    response.status_code = status
    return response
```

### Códigos de status usados

| Código | Quando                                              |
| ------ | --------------------------------------------------- |
| 200    | Sucesso                                             |
| 201    | Recurso criado                                      |
| 400    | Payload/validação inválida                          |
| 401    | Sem token ou token inválido/expirado                |
| 403    | Token válido mas papel sem permissão                |
| 404    | Recurso não encontrado                              |
| 409    | Conflito (ex: sensor_id/email duplicado, ambiente ocupado) |
| 500    | Falha inesperada (ex: scan de sensores)             |

### Autenticação e RBAC (Role-Based Access Control)

Existem três papéis no sistema: `admin_master`, `admin` e `visualizador`.

Decoradores em `app/routes/auth.py`:

```python
@main_bp.route("/api/...", methods=["GET"])
@login_required        # qualquer usuário autenticado
def rota(): ...

@main_bp.route("/api/...", methods=["POST"])
@admin_required        # apenas papéis 'admin' e 'admin_master'
def rota(): ...
```

Injetam o usuário em `g.usuario` (dict: `id`, `nome`, `email`, `papel`, ...).

Para operações destrutivas ou de gerenciamento (como CRUD de usuários), há validações granulares dentro das rotas para garantir que um `admin` não pode gerenciar ou promover usuários de mesmo ou maior nível administrativo (`admin` ou `admin_master`).

### CORS

O app adiciona automaticamente headers CORS (`Access-Control-Allow-Origin: *`) e cada grupo de rotas expõe endpoints `OPTIONS` (204) para preflight.

---

## Execução e Testes

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python main.py
```

Testes:

```powershell
python -m pytest -q
```

Fixtures disponíveis no `tests/conftest.py`:

| Fixture               | Descrição                                                     |
| --------------------- | ------------------------------------------------------------- |
| `app`                 | App Flask com banco temporário                                |
| `client_raw`          | Test client sem autenticação                                  |
| `client`              | Test client **autenticado como admin_master**                 |
| `admin_normal_client` | Test client **autenticado como admin (comum)**                |
| `auth_token`  | Token do admin                                                |
| `ambiente`    | Ambiente criado via API (autenticado)                         |