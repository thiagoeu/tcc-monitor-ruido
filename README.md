# NoiseRadar — Sistema de Monitoramento de Ruído

> Projeto acadêmico (TCC) de monitoramento de ruído em tempo real com sensor via app mobile, dashboard web e backend Flask.

---

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Modificações Recentes](#modificações-recentes)
4. [Pré-requisitos](#pré-requisitos)
5. [Instalação e Execução — Linux / Fedora](#instalação-e-execução--linux--fedora)
6. [Instalação e Execução — Windows](#instalação-e-execução--windows)
7. [App Mobile (Expo)](#app-mobile-expo)
8. [Simulador de Sensor (Mock)](#simulador-de-sensor-mock)
9. [Rotas principais da API](#rotas-principais-da-api)
10. [Problemas Comuns](#problemas-comuns)

---

## Visão Geral

O **NoiseRadar** é um sistema completo de monitoramento de ruído composto por:

| Componente | Tecnologia | Função |
|---|---|---|
| **Backend** | Python / Flask / SQLite | API REST + servir o frontend |
| **Frontend Web** | HTML / CSS / JavaScript | Dashboard e gráficos |
| **App Mobile** | React Native / Expo | Sensor via microfone do celular |
| **Mock** | Python | Simulador de sensor para testes |

---

## Estrutura do Projeto

```
tcc-monitor-ruido/
├── code/
│   ├── backend/          # API Flask + SQLite
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── routes.py
│   │   │   └── services/
│   │   └── main.py
│   ├── frontend/         # Dashboard Web (HTML/CSS/JS)
│   │   ├── index.html
│   │   ├── graficos.html
│   │   ├── css/style.css
│   │   ├── js/
│   │   └── asserts/      # Logos e imagens
│   ├── mobile/           # App Expo (React Native)
│   │   ├── src/
│   │   ├── App.js
│   │   ├── app.config.js
│   │   └── .env          # ← URL da API (configurar aqui)
│   └── mock/
│       └── sensor.py     # Simulador de sensor
└── requirements.txt
```

---

## Modificações Recentes

As alterações abaixo foram realizadas na branch `feature/ui-update-fixes`:

### 🎨 Identidade Visual — NoiseRadar
- **Nome do produto definido**: NoiseRadar
- **Logo transparente** (`logo_do_tcc_transparente.png`) adicionada à sidebar do dashboard
- Títulos das páginas atualizados para "NoiseRadar - Dashboard" e "NoiseRadar - Gráficos"
- Sidebar alargada para 240px para acomodar a logo horizontal

### 📊 Dashboard — Estados de Monitoramento
Os cards de ambiente agora exibem **3 estados fixos** e bem definidos:

| Estado | Condição | Cor |
|---|---|---|
| 🔴 **Acima do limite** | Sensor ativo com dB acima do limite configurado | Vermelho |
| 🟢 **Normal** | Sensor ativo dentro do limite | Verde |
| ⚫ **Sem medições** | Nenhuma sessão ativa / sensor offline | Cinza |

### 📱 App Mobile — Conectividade
- Header `bypass-tunnel-reminder: true` adicionado em todas as chamadas de API para evitar o interceptor do `localtunnel`
- Arquivo `.env` do mobile deve conter a URL correta do backend

### 🗑️ Salas Mock Removidas
- Ambientes de teste/mock foram removidos da interface — cadastre apenas ambientes reais

---

## Pré-requisitos

### Para o Backend e Mock

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Python | 3.10+ | `python --version` |
| pip | qualquer | `pip --version` |
| Git | qualquer | `git --version` |

### Para o App Mobile

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Expo Go | última | Instalar no celular pela loja |

---

## Instalação e Execução — Linux / Fedora

### 1. Clonar o repositório

```bash
git clone https://github.com/thiagoeu/tcc-monitor-ruido.git
cd tcc-monitor-ruido
```

### 2. Criar e ativar o ambiente virtual Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Você verá `(.venv)` no início do terminal quando ativo.

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

Se o arquivo `requirements.txt` não existir ou faltar alguma dependência:

```bash
pip install flask requests pyserial minimalmodbus
```

### 4. Executar o Backend

```bash
cd code/backend
python main.py
```

Saída esperada:

```
* Serving Flask app 'app'
* Running on http://127.0.0.1:5000
* Running on http://192.168.X.X:5000   ← IP da sua máquina na rede local
```

> ✅ O backend já serve o frontend automaticamente. Acesse `http://127.0.0.1:5000` no navegador.

### 5. Acessar o Dashboard Web

Abra no navegador:

```
http://127.0.0.1:5000           → Dashboard principal
http://127.0.0.1:5000/graficos.html  → Página de gráficos
```

### Instalar Node.js no Fedora (caso não tenha)

```bash
sudo dnf install nodejs npm -y
node --version
```

---

## Instalação e Execução — Windows

### 1. Clonar o repositório

Abra o **PowerShell** ou **Git Bash** e execute:

```powershell
git clone https://github.com/thiagoeu/tcc-monitor-ruido.git
cd tcc-monitor-ruido
```

### 2. Criar e ativar o ambiente virtual Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Se aparecer erro de execução de scripts, rode antes:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Instalar dependências Python

```powershell
pip install -r requirements.txt
```

Ou manualmente:

```powershell
pip install flask requests pyserial minimalmodbus
```

### 4. Executar o Backend

```powershell
cd code\backend
python main.py
```

Saída esperada:

```
* Running on http://127.0.0.1:5000
* Running on http://192.168.X.X:5000
```

### 5. Acessar o Dashboard Web

Abra no navegador:

```
http://127.0.0.1:5000
```

### Instalar Node.js no Windows (caso não tenha)

Baixe e instale em: [https://nodejs.org](https://nodejs.org) (versão LTS recomendada)

---

## App Mobile (Expo)

O app mobile usa o **microfone do celular** como sensor de decibéis e envia os dados ao backend.

### Pré-requisitos

- Node.js 18+ instalado na máquina
- App **Expo Go** instalado no celular ([Android](https://play.google.com/store/apps/details?id=host.exp.exponent) / [iOS](https://apps.apple.com/app/expo-go/id982107779))
- Celular e computador na **mesma rede Wi-Fi**

### 1. Instalar dependências do app

```bash
cd code/mobile
npm install
```

### 2. Configurar a URL do backend

Edite o arquivo `code/mobile/.env`:

```env
API_BASE_URL=http://SEU_IP_LOCAL:5000
```

> **Como descobrir o IP da sua máquina:**
> - **Linux/Fedora**: `ip addr show | grep "inet "` — use o IP da interface (ex: `192.168.1.15`)
> - **Windows**: `ipconfig` no CMD — use o "Endereço IPv4" da interface Wi-Fi/Ethernet
>
> **Exemplo**: `API_BASE_URL=http://192.168.1.15:5000`

### 3. Iniciar o app

**Opção A — Rede local (celular e PC na mesma rede Wi-Fi):**

```bash
npx expo start --clear
```

Escaneie o QR Code com o **Expo Go** no Android, ou com a **câmera** no iOS.

**Opção B — Tunnel (redes diferentes ou VPN):**

```bash
npx expo start --tunnel --clear
```

> ⚠️ Na primeira vez o Expo perguntará se instala o `@expo/ngrok` — responda **yes**.

### 4. Cadastrar um ambiente antes de medir

1. Acesse o dashboard web (`http://SEU_IP:5000`)
2. Na seção **"Cadastro de ambiente"**, preencha:
   - **Nome**: ex. "Lab Programação 1"
   - **Localização**: ex. "Vivência"
   - **Sensor ID**: ex. "Celular-01" ← este nome deve bater com o que você selecionar no app
   - **Limite dB**: ex. 65
3. Clique em **Salvar**
4. O ambiente aparecerá no app mobile para seleção

---

## Simulador de Sensor (Mock)

O mock simula um sensor enviando medições aleatórias ao backend — útil para testes sem celular.

### Linux / Fedora

```bash
# Com ambiente virtual ativo:
cd code
python mock/sensor.py --dynamic
```

### Windows

```powershell
# Com ambiente virtual ativo:
cd code
python mock\sensor.py --dynamic
```

Saída esperada:

```
✓ Modo DINÂMICO ativado
[Lab Programação 1] 72.4 dB → ALERTA
[Sala Teste] 58.1 dB → Normal
```

> O mock usa os ambientes já cadastrados no banco. Certifique-se de ter cadastrado ao menos um ambiente antes de rodar.

---

## Rotas principais da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/ambientes` | Lista todos os ambientes |
| GET | `/api/ambientes?ativo=1` | Lista ambientes ativos |
| POST | `/api/ambientes` | Cadastra novo ambiente |
| DELETE | `/api/ambientes/{id}` | Remove ambiente |
| POST | `/api/medicoes` | Envia uma medição |
| GET | `/api/medicoes` | Lista medições recentes |
| GET | `/api/monitoramento` | Estado atual de todos sensores |
| POST | `/api/sessoes` | Inicia sessão de medição |
| DELETE | `/api/sessoes/{sensor_id}` | Encerra sessão |
| PUT | `/api/sessoes/{sensor_id}/heartbeat` | Mantém sessão ativa |
| GET | `/api/alertas` | Lista alertas gerados |
| GET | `/api/relatorios/resumo` | Relatório de medições |

---

## Problemas Comuns

### ❌ `python: command not found` (Linux/Fedora)

Use `python3` no lugar de `python`:

```bash
python3 main.py
```

Ou crie um alias:

```bash
alias python=python3
```

---

### ❌ Porta 5000 já está em uso

**Linux:**

```bash
# Descobrir qual processo usa a porta:
lsof -i :5000

# Matar o processo (substitua XXXX pelo PID):
kill -9 XXXX
```

**Windows (PowerShell):**

```powershell
netstat -ano | findstr :5000
taskkill /PID XXXX /F
```

---

### ❌ App mobile diz "Algo deu errado"

1. Verifique se o backend está rodando: acesse `http://SEU_IP:5000` no navegador do celular
2. Certifique-se de que o IP no `.env` do mobile é o IP atual da máquina (pode mudar ao reconectar na rede)
3. Pare o Expo e reinicie com `--clear` para limpar o cache:
   ```bash
   npx expo start --clear
   ```

---

### ❌ App mobile não carrega as salas

- O backend precisa estar rodando
- Ao menos um ambiente precisa estar cadastrado no dashboard web
- O `.env` do mobile precisa apontar para o IP correto

---

### ❌ JSON Parse error no app mobile

Ocorre quando o app recebe uma página HTML em vez de JSON (ex: página de aviso do localtunnel).

✅ **Solução já aplicada**: todas as requisições do app enviam o header `bypass-tunnel-reminder: true`.

Se persistir com `--tunnel`, verifique se o `npx expo start` foi reiniciado após a mudança no `.env`.

---

### ❌ Erro de autenticação no `git push`

O repositório usa SSH. Certifique-se de que sua chave SSH está cadastrada no GitHub:

```bash
# Ver sua chave pública:
cat ~/.ssh/id_ed25519.pub
```

Cole o conteúdo em: **GitHub → Settings → SSH and GPG keys → New SSH key**

---

## 🛠️ Tecnologias

- **Python 3.10+** / **Flask** / **SQLite**
- **HTML5** / **CSS3** / **JavaScript (ES6+)**
- **React Native** / **Expo SDK 54**
- **expo-av** (captura de áudio)
- **Chart.js** (gráficos no dashboard)

---

## 👤 Autor

Projeto acadêmico — TCC — Monitoramento de Ruído  
GitHub: [@thiagoeu](https://github.com/thiagoeu)
