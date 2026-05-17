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
