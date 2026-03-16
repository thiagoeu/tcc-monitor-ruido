# TCC Monitor de Ruído (Raspberry Pi 3 B+)

Aplicação de monitoramento acústico para execução **headless** no Raspberry Pi 3 B+, com baixo custo operacional.

## Recursos

- Backend Flask + SQLite local
- Frontend separado em arquivos (`HTML`, `CSS`, `JS`)
- Dashboard com seções em acordeão para reduzir poluição visual
- Cadastro e exclusão de ambientes/sensores
- Monitoramento em tempo real
- Alertas de limite excedido
- Gráficos leves (tendência e percentual de alertas)
- Relatórios com percentuais por período (resumo + download em TXT)

## Estrutura

- `code/backend/main.py`: entrypoint da API
- `code/backend/app/__init__.py`: factory da aplicação
- `code/backend/app/database.py`: conexão e bootstrap do banco
- `code/backend/app/services.py`: regras de negócio e relatórios
- `code/backend/app/routes.py`: rotas HTTP
- `code/frontend/index.html`: estrutura da interface
- `code/frontend/assets/style.css`: estilos da interface
- `code/frontend/assets/app.js`: lógica da interface
- `code/mock/sensor.py`: mock de sensores
- `code/deploy/*.service`: serviços `systemd`

## Requisitos no Raspberry

```bash
sudo apt update
sudo apt install -y python3-venv python3-full git
```

## Instalação

```bash
cd ~
git clone git@github.com:thiagoeu/tcc-monitor-ruido.git
cd tcc-monitor-ruido
git checkout code

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Execução manual

### Terminal 1 (backend)

```bash
cd ~/tcc-monitor-ruido
source .venv/bin/activate
python code/backend/main.py
```

### Terminal 2 (mock)

#### Opção A: Modo Dinâmico (Recomendado)

O mock busca **automaticamente** todos os sensores cadastrados no backend, independente do nome. Novos sensores adicionados pelo dashboard são detectados a cada 30 segundos.

```bash
cd ~/tcc-monitor-ruido
source .venv/bin/activate
python code/mock/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --interval 5 --dynamic
```

**Vantagens:**
- Sensores adicionados no dashboard geram leituras automaticamente
- Não precisa reiniciar o mock ao cadastrar novo sensor
- Nomenclatura livre: `my-sensor-01`, `Lab_A`, `Sala_Principal` - qualquer nome funciona
- Faixa de dB calculada dinamicamente baseada no `limite_db` de cada ambiente

**Output esperado:**
```
Iniciando mock: intervalo=5s, modo_dinâmico=True
✓ Modo DINÂMICO ativado: novos sensores serão detectados automaticamente
Enviando para: http://127.0.0.1:5000/api/medicoes
[Ciclo 1] ✓ Detectados 2 sensor(es) do backend
[Sala Principal] 68.5 dB @ 45-75 -> OK
[Laboratório] 52.3 dB @ 45-85 -> OK
```

#### Opção B: Modo Legado (Configuração manual)

Se preferir especificar sensores explicitamente via linha de comando:

```bash
cd ~/tcc-monitor-ruido
source .venv/bin/activate
python code/mock/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --interval 5 --sensors e06a-001:45:82,e06a-002:35:78
```

**Formato:** `sensorID:min_dB:max_dB,sensorID2:min_dB:max_dB,...`

⚠️ **Aviso:** Neste modo, sensores novos cadastrados no dashboard **NÃO** geram leituras. Requer reiniciar o mock com a nova configuração.

---

## Como funcionam os sensores

1. **Sem modo `--dynamic`:** O mock só gera leituras para sensores configurados via `--sensors`
   - Problema: Novo sensor cadastrado no dashboard não recebe simulações
   - Solução: Reiniciar mock com sensor adicionado

2. **Com modo `--dynamic`:** O mock faz `GET /api/ambientes` a cada 30 segundos
   - Busca lista atualizada de sensores do backend
   - Extrai `sensor_id` e `limite_db` de cada ambiente
   - Calcula faixa de dB automaticamente: `[limite - 20, limite + 10]`
   - Gera leituras contínuas para todos (12% de chance de spike +5-12 dB acima da faixa)

**Nome dos sensores:** No dashboard, você pode usar qualquer nomenclatura. O backend aceita qualquer `sensor_id`. Exemplos válidos:
- `e06a-001` (padrão)
- `Lab_A`, `Sala Principal`, `my-sensor-01`
- Caracteres especiais são aceitos

## Acesso ao dashboard

Abra em outro dispositivo da mesma rede local:

```text
http://IP_DO_RASPBERRY:5000
```

Exemplo:

```text
http://192.168.18.211:5000
```

## Relatórios

### Resumo JSON por janela de horas

```bash
curl "http://127.0.0.1:5000/api/relatorios/resumo?hours=24"
```

### Download do relatório TXT

```bash
curl -L "http://127.0.0.1:5000/api/relatorios/txt?hours=24" -o relatorio.txt
```

No dashboard, a seção **Relatórios** já mostra percentuais e permite baixar o TXT.

## API principal

- `GET /health`
- `GET /api/ambientes`
- `POST /api/ambientes`
- `PUT /api/ambientes/{id}`
- `DELETE /api/ambientes/{id}`
- `POST /api/medicoes`
- `GET /api/monitoramento`
- `GET /api/alertas`
- `GET /api/relatorios/resumo?hours=24`
- `GET /api/relatorios/txt?hours=24`

## Rodar no boot com systemd

Os serviços em `code/deploy` estão ajustados para:

- usuário `ruido`
- venv em `/home/ruido/tcc-monitor-ruido/.venv`
- modo **dinâmico** do mock (detecta sensores automaticamente do backend)

Instalação:

```bash
cd ~/tcc-monitor-ruido
sudo cp code/deploy/monitor-ruido-backend.service /etc/systemd/system/
sudo cp code/deploy/monitor-ruido-mock.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable monitor-ruido-backend.service
sudo systemctl enable monitor-ruido-mock.service
sudo systemctl restart monitor-ruido-backend.service
sudo systemctl restart monitor-ruido-mock.service
```

**Para usar modo legado (sensores fixos):** Editar `/etc/systemd/system/monitor-ruido-mock.service` e remover `--dynamic`:

```ini
ExecStart=/home/ruido/tcc-monitor-ruido/.venv/bin/python ... --sensors e06a-001:45:82,e06a-002:35:78
```

Depois recarregar:

```bash
sudo systemctl daemon-reload
sudo systemctl restart monitor-ruido-mock.service
```

Logs:

```bash
sudo journalctl -u monitor-ruido-backend.service -f
sudo journalctl -u monitor-ruido-mock.service -f
```

## Observações

- O backend faz bootstrap automático dos sensores padrão `e06a-001` e `e06a-002`.
- Para testes de TCC, o servidor Flask de desenvolvimento é suficiente.
- Comando correto para executar é `python`, não `run`.
