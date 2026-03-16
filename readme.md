# TCC Monitor de Ruído (Raspberry Pi 3 B+)

Sistema de monitoramento acústico para Raspberry Pi (sem interface gráfica), com:

- Backend Flask + SQLite local
- Dashboard web acessível pela rede local
- Mock de sensores de ruído (E06A simulado)
- Execução manual ou automática com `systemd`

## Estrutura do projeto

- `code/backend/main.py`: API e banco local
- `code/frontend/index.html`: dashboard
- `code/mock/sensor.py`: simulador de sensores
- `code/deploy/*.service`: serviços para boot automático

## 1) Pré-requisitos no Raspberry

```bash
sudo apt update
sudo apt install -y python3-venv python3-full git
```

## 2) Clonar e preparar ambiente

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

## 3) Rodar manualmente (teste rápido)

### Terminal 1 — Backend

```bash
cd ~/tcc-monitor-ruido
source .venv/bin/activate
python code/backend/main.py
```

Você deve ver algo como:

- `Running on http://127.0.0.1:5000`
- `Running on http://IP_DO_RASPBERRY:5000`

### Terminal 2 — Mock de sensores

```bash
cd ~/tcc-monitor-ruido
source .venv/bin/activate
python code/mock/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --interval 5 --sensors e06a-001:45:82,e06a-002:35:78
```

## 4) Abrir dashboard em outro dispositivo

No celular/notebook na mesma rede local, acesse:

```text
http://IP_DO_RASPBERRY:5000
```

Exemplo:

```text
http://192.168.18.211:5000
```

## 5) Resolver erro `404 sensor_id não encontrado`

Se aparecer no mock:

- `e06a-002 erro ao enviar: API retornou 404 ...`

faça:

```bash
curl http://127.0.0.1:5000/api/ambientes
```

Se `e06a-002` não existir, cadastre:

```bash
curl -X POST http://127.0.0.1:5000/api/ambientes \
  -H "Content-Type: application/json" \
  -d '{"nome":"Biblioteca","localizacao":"Bloco A","sensor_id":"e06a-002","limite_db":60}'
```

> Nesta branch, o backend já tenta criar automaticamente `e06a-001` e `e06a-002` no bootstrap.

## 6) Rodar automático no boot (systemd)

Arquivos já prontos para usuário `ruido` e `.venv`:

- `code/deploy/monitor-ruido-backend.service`
- `code/deploy/monitor-ruido-mock.service`

Instalação:

```bash
cd ~/tcc-monitor-ruido
sudo cp code/deploy/monitor-ruido-backend.service /etc/systemd/system/
sudo cp code/deploy/monitor-ruido-mock.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable monitor-ruido-backend.service
sudo systemctl enable monitor-ruido-mock.service
sudo systemctl start monitor-ruido-backend.service
sudo systemctl start monitor-ruido-mock.service
```

Ver status/logs:

```bash
sudo systemctl status monitor-ruido-backend.service
sudo systemctl status monitor-ruido-mock.service
sudo journalctl -u monitor-ruido-backend.service -f
sudo journalctl -u monitor-ruido-mock.service -f
```

## 7) Comandos úteis de validação

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/api/monitoramento?limit=10
```

## Observações

- `run main.py` não é comando válido no bash; use `python main.py`.
- O aviso do Flask sobre ambiente de desenvolvimento é esperado para testes do TCC.
