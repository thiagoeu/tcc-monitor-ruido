# Documentação de Execução — Sistema de Monitoramento de Ruído

## Visão Geral

Este projeto é um sistema de monitoramento de ruído desenvolvido com:

- Backend em Python utilizando Flask
- Banco de dados SQLite
- Frontend HTML/CSS/JavaScript
- Mock de sensores para simulação de medições

O sistema permite:

- Cadastro de ambientes
- Monitoramento em tempo real
- Visualização de gráficos
- Geração de alertas
- Relatórios de medições

---

# Estrutura do Projeto

```text
code
┣ backend
┃ ┣ app
┃ ┃ ┣ database.py
┃ ┃ ┣ routes.py
┃ ┃ ┣ services.py
┃ ┃ ┗ __init__.py
┃ ┗ main.py
┣ frontend
┣ mock
┗ deploy
```

---

# Pré-requisitos

Antes de iniciar o projeto, é necessário possuir instalado:

- Python 3.10+
- pip
- Git

Verificar versões:

```bash
python --version
pip --version
git --version
```

---

# Clonando o Projeto

```bash
git clone <URL_DO_REPOSITORIO>
```

Entrar na pasta:

```bash
cd tcc/code/backend
```

---

# Criando Ambiente Virtual

## Windows PowerShell

Criar ambiente virtual:

```powershell
python -m venv .venv
```

Ativar ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Após ativar, o terminal deve exibir algo semelhante:

```text
(.venv) PS C:\projeto>
```

---

# Instalando Dependências

Instalar dependências necessárias:

```powershell
pip install flask requests
```

Opcionalmente, gerar arquivo requirements.txt:

```powershell
pip freeze > requirements.txt
```

---

# Executando o Backend

Dentro da pasta:

```text
code/backend
```

Executar:

```powershell
python main.py
```

Saída esperada:

```text
* Running on http://127.0.0.1:5000
```

---

# Acessando o Sistema

## Dashboard Principal

Abrir no navegador:

```text
http://127.0.0.1:5000
```

## Página de Gráficos

```text
http://127.0.0.1:5000/graficos.html
```

---

# Executando o Mock de Sensores

O mock simula sensores reais enviando medições para o backend.

Abrir um NOVO terminal.

Ir para a raiz do projeto:

```powershell
cd code
```

Ativar o ambiente virtual:

```powershell
backend\.venv\Scripts\Activate.ps1
```

Executar o mock:

```powershell
python mock\sensor.py --dynamic
```

Saída esperada:

```text
✓ Modo DINÂMICO ativado
[Sala Principal] 72.4 dB -> ALERTA
```

---

# Sensor físico via UART do Raspberry Pi

O projeto também suporta um sensor Modbus RTU físico conectado diretamente na UART do Raspberry Pi 3 B+.

## Conexão física

Se o sensor trabalhar em 5V no TX, use divisor de tensão ou conversor de nível lógico antes de conectar ao RX do Raspberry Pi.

| Pino do Sensor | Pino do Raspberry Pi 3B (físico) | Nome no Raspberry Pi |
| --- | --- | --- |
| VCC | Pino 2 ou 4 | 5V |
| GND | Pino 6, 9, 14, 20, 25, 30, 34 ou 39 | GND |
| TX | Pino 10 | GPIO15 (RX) |
| RX | Pino 8 | GPIO14 (TX) |

## Habilitando a serial

No Raspberry Pi, execute:

```bash
sudo raspi-config
```

Em Interface Options, abra Serial Port e responda:

- Console de login pela serial: Não
- Hardware da serial: Sim

Depois, desative o Bluetooth na UART adicionando a linha abaixo ao final de `/boot/config.txt` ou `/boot/firmware/config.txt`:

```text
dtoverlay=disable-bt
```

Reinicie o sistema:

```bash
sudo reboot
```

Após isso, a porta serial fica disponível em `/dev/ttyAMA0`.

## Execução do leitor físico

O script físico já usa `/dev/ttyAMA0` por padrão, com Modbus RTU em `9600 8N1`.

Antes de configurar, descubra quais portas existem e quais IDs Modbus respondem.

Listar portas seriais detectadas:

```bash
cd code
python sensor/scan_modbus_ids.py --list-ports
```

Escanear IDs Modbus na UART do Raspberry Pi:

```bash
cd code
python sensor/scan_modbus_ids.py --port /dev/ttyAMA0 --baudrate 9600 --start-id 1 --end-id 32 --registers 0,1
```

Se nao encontrar, tente input register (function code 4):

```bash
cd code
python sensor/scan_modbus_ids.py --port /dev/ttyAMA0 --baudrate 9600 --start-id 1 --end-id 32 --registers 0,1 --function-code 4
```

Importante:
- `sensor_id` no dashboard e um identificador textual (ex: `lab-a-01`).
- `--slave-addr` no script do sensor e o ID Modbus descoberto no scanner.

Exemplo:

```bash
cd code
python sensor/sensor.py --api-url http://127.0.0.1:5000/api/medicoes --port /dev/ttyAMA0 --baudrate 9600 --slave-addr 1 --register 0
```

Esse modo não usa os sinais de controle do RS485, porque a UART TTL do Raspberry Pi faz a comunicação diretamente.

---

# Banco de Dados

O sistema utiliza SQLite.

O banco é criado automaticamente em:

```text
code/backend/ruido.db
```

As tabelas também são criadas automaticamente durante a inicialização:

- ambientes
- medicoes
- alertas

---

# Sensores Padrão

O sistema já cria automaticamente dois ambientes:

| Ambiente       | Sensor   |
| -------------- | -------- |
| Sala Principal | e06a-001 |
| Biblioteca     | e06a-002 |

---

# Rotas Principais da API

## Health Check

```text
GET /health
```

## Listar Ambientes

```text
GET /api/ambientes
```

## Criar Ambiente

```text
POST /api/ambientes
```

## Criar Medição

```text
POST /api/medicoes
```

## Monitoramento

```text
GET /api/monitoramento
```

## Alertas

```text
GET /api/alertas
```

## Relatórios

```text
GET /api/relatorios/resumo
```

---

# Fluxo Geral do Sistema

```text
Mock de Sensores
        ↓
Backend Flask
        ↓
SQLite
        ↓
Frontend Dashboard
```

---

# Possíveis Problemas

## Erro: Flask não encontrado

Instalar dependência:

```powershell
pip install flask
```

---

## Erro: requests não encontrado

Instalar:

```powershell
pip install requests
```

---

## Porta 5000 já está em uso

Encerrar o processo utilizando a porta ou alterar a porta no arquivo:

```text
backend/main.py
```

Variável:

```python
APP_PORT
```

---

# Deploy Linux (Raspberry Pi)

O projeto já possui arquivos systemd:

```text
monitor-ruido-backend.service
monitor-ruido-mock.service
```

Esses arquivos permitem iniciar automaticamente:

- Backend Flask
- Mock de sensores

via systemctl.

---

# Tecnologias Utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

---

# Autor

Projeto acadêmico de monitoramento de ruído utilizando Raspberry Pi e sensores simulados.
