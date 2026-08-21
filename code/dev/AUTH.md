# Sistema de Login — NoiseRadar

## Visão Geral

Autenticação por **Token Bearer** (token opaco armazenado no banco). Permite três papéis (RBAC):

| Papel          | Permissões                                        |
| -------------- | ------------------------------------------------- |
| `admin_master` | Acesso total + cria/edita qualquer usuário        |
| `admin`        | Acesso total + cria/edita apenas visualizadores   |
| `visualizador` | Apenas visualiza dashboards, relatórios e alertas |

Sem dependências novas: hash de senha via `werkzeug.security` (já vem com Flask) e token via `secrets` (stdlib).

---

## Credenciais Iniciais (Seed)

Um administrador mestre padrão é criado automaticamente no primeiro startup do backend.

| Campo  | Valor padrão                 |
| ------ | ---------------------------- |
| E-mail | `admin@noiseradar.local`     |
| Senha  | `admin123`                   |
| Papel  | `admin_master`               |
| Nome   | `Administrador`              |

> ⚠️ **Altere a senha padrão em produção** usando as variáveis de ambiente abaixo.

Para definir credenciais personalizadas antes de subir o servidor:

```powershell
$env:ADMIN_EMAIL="seu@email.com"
$env:ADMIN_SENHA="senha-forte"
$env:ADMIN_NOME="Seu Nome"
python main.py
```

No Linux/Raspberry Pi (bash):

```bash
ADMIN_EMAIL=seu@email.com ADMIN_SENHA=senha-forte python main.py
```

---

## Atualizando o Banco Local

Não é necessário migração manual. Na inicialização, `init_db()` executa
`CREATE TABLE IF NOT EXISTS usuarios` e o seed insere o admin somente se o
e-mail ainda não existir — seu `ruido.db` é atualizado sozinho.

Para aplicar/verificar de forma explícita:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -c "from app import create_app; create_app(); print('banco atualizado')"
```

Conferir o usuário criado:

```powershell
python -c "import sqlite3; con=sqlite3.connect('ruido.db'); [print(r) for r in con.execute('SELECT id,email,papel,ativo FROM usuarios')]"
```

### Estrutura da tabela `usuarios`

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT 'visualizador',
    ativo INTEGER NOT NULL DEFAULT 1,
    token TEXT,
    token_expira TEXT,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);
```

---

## Endpoints de Autenticação

| Método | Rota                 | Descrição                                    |
| ------ | -------------------- | -------------------------------------------- |
| POST   | `/api/auth/login`    | Body `{email, senha}` → retorna `{token, expira_em, usuario}` |
| POST   | `/api/auth/logout`   | Revoga o token atual                         |
| GET    | `/api/auth/me`       | Retorna o usuário autenticado                |
| GET    | `/api/usuarios`      | Lista usuários — **somente admin**           |
| POST   | `/api/usuarios`      | Cria usuário — **somente admin**             |

Exemplo de login via curl:

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@noiseradar.local","senha":"admin123"}'
```

Criar um usuário visualizador (com o token retornado no login):

```bash
curl -X POST http://127.0.0.1:5000/api/usuarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"nome":"Maria","email":"maria@noiseradar.local","senha":"senha123","papel":"visualizador"}'
```

### Configuração do token

| Env var             | Default | Descrição            |
| ------------------- | ------- | -------------------- |
| `APP_TOKEN_TTL_HORAS` | `168` | Validade do token em horas (7 dias) |

---

## Rotas Protegidas e Abertas

**Protegidas (exigem `Authorization: Bearer <token>`):**

- `POST/PUT/DELETE /api/ambientes`
- `GET /api/monitoramento`
- `GET /api/alertas`
- `GET /api/relatorios/resumo` e `/api/relatorios/txt`
- `GET /api/sensores/fisicos`
- `GET /api/sessoes`

**Abertas (usadas pelo app mobile e sensores/mock):**

- `GET /api/ambientes`
- `POST /api/medicoes`
- `POST/DELETE/PUT` em `/api/sessoes` (ocupar, liberar, heartbeat)

---

## Frontend

- `frontend/login.html` — página de login.
- `frontend/js/auth.js` — token no `localStorage` (`noiseradar_token`), login/logout/guard.
- Dashboards (`/` e `/graficos.html`) redirecionam para `/login.html` sem sessão e exibem botão **Sair** na sidebar.
- Em resposta `401`, o token é limpo e o usuário é redirecionado ao login.

---

## Testes

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Cobertura: login, logout, `me`, token inválido/expirado, 401 em rotas protegidas, criação de usuário admin-only (403 para visualizador) e email duplicado (409).