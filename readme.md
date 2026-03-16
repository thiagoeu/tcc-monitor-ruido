# Sistema de Monitoramento de Ruído (Raspberry Pi 3 B+)

Implementação enxuta para ambiente **headless** (sem interface gráfica), com:

- Backend Flask + SQLite local
- Dashboard web leve (acessado de outro dispositivo)
- Mock de múltiplos sensores de ruído
- Estrutura pronta para rodar como serviço no boot (`systemd`)

## Estrutura

- `code/backend/main.py`: API principal e banco SQLite
- `code/frontend/index.html`: dashboard de monitoramento
- `code/mock/sensor.py`: simulador de sensores
- `code/deploy/*.service`: serviços para Raspberry Pi

## Requisitos

- Raspberry Pi 3 B+ com Raspberry Pi OS Lite
- Python 3.9+
- Rede local para acessar o dashboard

## Subir localmente (teste rápido)

Na pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 code/backend/main.py
```

Em outro terminal:

```bash
source .venv/bin/activate
python3 code/mock/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --interval 5 --sensors e06a-001:45:82,e06a-002:35:78
```

Abra no navegador (outro PC/celular na mesma rede):

```text
http://IP_DO_RASPBERRY:5000
```

## API principal

- `GET /health`: saúde do serviço
- `GET /api/ambientes`: lista ambientes
- `POST /api/ambientes`: cadastra ambiente
- `PUT /api/ambientes/{id}`: atualiza ambiente
- `POST /api/medicoes`: recebe leitura (`sensor_id`, `db`)
- `GET /api/monitoramento`: snapshot para dashboard
- `GET /api/alertas`: lista alertas

Exemplo de cadastro de ambiente:

```bash
curl -X POST http://127.0.0.1:5000/api/ambientes \
  -H "Content-Type: application/json" \
  -d '{"nome":"Biblioteca","localizacao":"Bloco A","sensor_id":"e06a-002","limite_db":60}'
```

Exemplo de envio de medição:

```bash
curl -X POST http://127.0.0.1:5000/api/medicoes \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"e06a-001","db":72.4}'
```

## Rodar no boot com systemd (Raspberry)

Copie os serviços:

```bash
sudo cp code/deploy/monitor-ruido-backend.service /etc/systemd/system/
sudo cp code/deploy/monitor-ruido-mock.service /etc/systemd/system/
```

> Ajuste os caminhos nos arquivos `.service` caso o projeto não esteja em `/home/pi/tcc-monitor-ruido`.

Ative e inicie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable monitor-ruido-backend.service
sudo systemctl enable monitor-ruido-mock.service
sudo systemctl start monitor-ruido-backend.service
sudo systemctl start monitor-ruido-mock.service
```

Logs:

```bash
sudo journalctl -u monitor-ruido-backend.service -f
sudo journalctl -u monitor-ruido-mock.service -f
```

## Próximo passo para sensor real RS485

Com o mock validado, o passo seguinte é trocar o envio de `code/mock/sensor.py` por leitura real via conversor USB-RS485 e protocolo do E06A, mantendo a mesma rota `POST /api/medicoes`.
