# Testes do Backend (Flask)

Como rodar e entender a suíte de testes automatizada do backend (`code/backend`).

## O que é testado

A suíte usa `pytest` com um banco SQLite **temporário e isolado por teste** (cada teste cria o próprio `.db` numa pasta temporária e o remove no final — o `ruido.db` de desenvolvimento nunca é tocado).

| Arquivo | O que cobre |
|---|---|
| `tests/test_health.py` | Endpoint `GET /health` |
| `tests/test_ambientes.py` | CRUD de ambientes: criar, listar (com filtro `ativo`), atualizar, excluir, validações e conflitos (`sensor_id` duplicado) |
| `tests/test_sessoes.py` | Reserva de ambiente (`POST /api/sessoes`), heartbeat, liberação, conflito de dispositivo, expiração por TTL e flag `em_uso` |
| `tests/test_medicoes.py` | Envio de medições, geração de alertas quando excede o limite, sensor inativo/desconhecido, monitoramento e alertas |
| `tests/test_relatorios.py` | Resumo (`GET /api/relatorios/resumo`) e relatório em texto (`GET /api/relatorios/txt`) |
| `tests/test_monitoramento_service.py` | Validações do scan de sensores Modbus físicos (sem tocar hardware) |

## Pré-requisitos

- Python 3.12+ (o projeto usa 3.13 no `.venv` local)
- Dependências de desenvolvimento instaladas no venv (pytest + deps do app):

```powershell
# na pasta code/backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Como rodar

```powershell
# na pasta code/backend (ativa o .venv primeiro)
.\.venv\Scripts\python.exe -m pytest
```

Comandos úteis:

| Ação | Comando |
|---|---|
| Rodar todos os testes | `.\.venv\Scripts\python.exe -m pytest` |
| Rodar um arquivo só | `.\.venv\Scripts\python.exe -m pytest tests\test_ambientes.py` |
| Rodar um teste específico | `.\.venv\Scripts\python.exe -m pytest tests\test_sessoes.py::test_ocupar_ambiente` |
| Ver cada teste por nome (`-v`) | `.\.venv\Scripts\python.exe -m pytest -v` |
| Rodar sem captura (ver prints/logs) | `.\.venv\Scripts\python.exe -m pytest -s` |
| Rodar só os que falharam | `.\.venv\Scripts\python.exe -m pytest --lf` |

> Dica: se o `python` já estiver ativado no terminal (`.\Scripts\Activate.ps1`), basta usar `python -m pytest`.

## Como funciona

- **`tests/conftest.py`** fornece as fixtures:
  - `app` — cria a aplicação Flask apontando `DB_PATH` para um arquivo temporário (`tmp_path`) e liga `TESTING=True` (exceções viram falhas de teste em vez de erros 500 silenciosos).
  - `client` — um `test_client` do Flask para chamar as rotas.
  - `ambiente` — já cria um ambiente válido via API (`sensor_id` fixo `sensor-teste-1`, limite 65 dB).
  - `limpar_sessoes` — limpa as sessões em memória antes/depois de cada teste (as sessões ficam num dicionário global, então precisam de isolamento).
- **Banco temporário:** a `create_app` agora aceita `config_overrides`, que permite sobrescrever a config (como `DB_PATH`) sem afetar a execução normal.

## Detalhes do que cada grupo valida

### Ambientes
- Criar com dados válidos retorna **201** e o objeto criado (com `id`, `created_at` e `limite_db` padrão 65 quando não informado).
- Campos obrigatórios ausentes → **400**; `sensor_id` duplicado → **409**; `limite_db` não numérico ou negativo → **400**.
- Atualizar com `nome` vazio → **400**; sensor duplicado → **409**; ambiente inexistente → **404**.
- Excluir ambiente remove medições e alertas associados; inexistente → **404**.

### Sessões
- Ocupar ambiente retorna `{ok: true}`; já ocupado por outro device → **409**; mesmo device renova a sessão sem erro.
- Heartbeat renova TTL; sem `device_id` → **400**; sessão não pertence ao device → **404**.
- Liberar devolve `{ok: true}`/`{ok: false}` dependendo se a sessão pertencia ao device.
- O campo `em_uso` do ambiente reflete a sessão ativa, e uma sessão com TTL expirado libera o ambiente automaticamente.

### Medições / monitoramento
- Medição dentro do limite → `excedeu_limite: false` e **sem alerta**; acima do limite → **gera alerta** (visível em `GET /api/alertas`).
- Sensor desconhecido ou ambiente inativo → **404**; `sensor_id` ausente ou `db` inválido → **400**.
- `GET /api/monitoramento` retorna ambientes, medições, alertas, última medição por ambiente; `limit` inválido cai para o default e valores são limitados entre min/max.

### Relatórios
- Resumo sem dados → contadores zerados e `ambientes: []`.
- Resumo com medições calcula total, alertas, percentual, média/pico/mínimo (por ambiente e geral).
- `hours` inválido usa default 24; fora do range é limitado (1..720).
- `GET /api/relatorios/txt` devolve `text/plain` com `Content-Disposition: attachment` e o conteúdo do relatório.

### Scan físico (Modbus)
- Sem dependências de serial → `RuntimeError`.
- Faixa de IDs inválida, `function_code` ≠ 3/4 ou lista de registradores vazia → `ValueError`.
- Nenhum teste faz chamada real a porta serial/hardware.

## Estrutura esperada

```
code/backend/
├── app/                  # aplicação (não alterada além de config_overrides)
├── tests/                # suíte de testes
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_ambientes.py
│   ├── test_sessoes.py
│   ├── test_medicoes.py
│   ├── test_relatorios.py
│   └── test_monitoramento_service.py
├── pytest.ini            # configuração do pytest (descobre tests/)
├── requirements.txt      # dependências de execução
└── requirements-dev.txt  # execução + pytest
```

## Integração com o resto do sistema

- O frontend consome `GET /api/ambientes`, `POST /api/medicoes` e o fluxo de sessões (`POST/DELETE/PUT /api/sessoes`) — tudo isso está coberto aqui.
- O app mobile (`code/mobile`) tem seus próprios testes (Jest) em `code/mobile/__tests__/`.
