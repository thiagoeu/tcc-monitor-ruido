# Guia de Rebuild do App (EAS Build)

Como gerar um novo APK instalável do app **soundtracker** sempre que precisar.

## Pré-requisitos (só na primeira vez)

- Conta Expo gratuita: https://expo.dev/signup
- EAS CLI instalado e logado:

```powershell
npm install -g eas-cli
eas login
```

## Passo a passo a cada rebuild

### 1. Descobrir o IP atual do PC

```powershell
ipconfig
```

Anote o IPv4 da rede **Wi-Fi** (ex.: `192.168.0.4`). Se mudou desde o último build, atualize o `.env`.

### 2. Ajustar a URL do backend (se o IP mudou)

Arquivo: `mobile\.env`

```
API_BASE_URL=http://<SEU_IP>:5000
```

Esse valor fica **embutido no APK** — se o IP do PC mudar, é obrigatório rebuildar.

### 3. Ligar o backend no PC

```powershell
# na pasta backend
python main.py
```

O backend já escuta em `0.0.0.0:5000` (acessível pela rede local). O celular e o PC precisam estar na **mesma rede Wi-Fi**.

> Se der "não conecta": libere a porta 5000 no Firewall do Windows
> (regra de **entrada**, TCP, porta 5000) e rode o backend.

### 4. Rodar o build

Na pasta `mobile`:

```powershell
eas build -p android --profile preview
```

- O perfil `preview` gera um **APK** (instalável direto).
- O primeiro build cria o keystore de assinatura automaticamente.
- Ao final, o terminal mostra o link do APK (ou use `eas build:list`).

### 5. Instalar no celular

1. Abra o link do APK no celular e baixe o arquivo.
2. Habilite "Instalar de fontes desconhecidas" quando o Android pedir.
3. Instale e abra o app.
4. Selecione o ambiente e inicie a medição.

### 6. Teste rápido de conexão (opcional, antes do build)

No navegador do **celular**, abra:

```
http://<SEU_IP>:5000/api/ambientes?ativo=1
```

Deve retornar um JSON com a lista de ambientes.

## Comandos úteis

| Ação | Comando |
|---|---|
| Iniciar app em dev (Expo Go) | `npx expo start` |
| Listar builds já feitos | `eas build:list` |
| Baixar/ver último build | `eas build:list --limit 1` |
| Apagar build antigo | `eas build:delete` |
| Deslogar | `eas logout` |

## Custos / limites

- Plano Free: **15 builds Android/mês**, zera dia 1º de cada mês.
- Não usa cartão; se esgotar, espera o reset (ou build local, grátis).

## Arquivos importantes

| Arquivo | Papel |
|---|---|
| `mobile\app.config.js` | Identificador do app, cleartext HTTP, `projectId`, `apiBaseUrl` default |
| `mobile\.env` | `API_BASE_URL` (usado no build) |
| `mobile\eas.json` | Perfil `preview` que gera APK |
| `backend\main.py` | Servidor (porta 5000, host `0.0.0.0`) |