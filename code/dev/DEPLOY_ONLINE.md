# Deploy Online — Raspberry Pi 3 B+ (SoundTracker)

Backend + frontend rodando no Raspberry Pi, expostos na internet via **ngrok** (URL estável, sem domínio próprio), com o app mobile instalado em celulares acessando de qualquer rede.

## Arquitetura

```
Celulares (app) ──HTTPS──> https://<seu-nome>.ngrok-free.app ──> ngrok ──> Pi 3 B+ (Flask :5000)
                                                                          ├── frontend/
                                                                          └── ruido.db (SQLite)
```

## Parte 1 — Preparar o Pi

1. Raspberry Pi OS 64-bit (Pi 3 B+), SSH habilitado.
2. Instalar dependências:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-venv curl unzip
   ```
3. Copiar `backend/` + `frontend/` para o Pi (scp, git clone ou USB).
4. Rodar:
   ```bash
   cd backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
5. Teste: `curl http://localhost:5000/api/ambientes?ativo=1`.

> `minimalmodbus`/`pyserial` são opcionais (medições vêm dos celulares).

## Parte 2 — Expor na internet (ngrok, URL estável)

1. Conta grátis em ngrok.com → token de autenticação.
2. Instalar e configurar no Pi:
   ```bash
   # baixar binário arm64 do ngrok, extrair para /usr/local/bin
   ngrok config add-authtoken <SEU_TOKEN>
   ```
3. Reservar domínio estático no painel (ex.: `ruido-tcc.ngrok-free.app`).
4. Rodar: `ngrok http 5000 --domain=ruido-tcc.ngrok-free.app`.

> URL fixa → o app é buildado apenas 1 vez.

## Parte 3 — Auto-iniciar no boot (systemd)

Dois serviços em `/etc/systemd/system/`:

- `soundtracker.service` → Flask (ExecStart com o venv).
- `ngrok.service` → ngrok apontando para o domínio estático.

Habilitar com `systemctl enable`. Pi liga → já fica online.

## Parte 4 — Rebuild do app (uma vez)

Em `mobile\` no PC:
1. Editar `mobile\.env`:
   ```
   API_BASE_URL=https://ruido-tcc.ngrok-free.app
   ```
2. Buildar:
   ```powershell
   eas build -p android --profile preview
   ```
3. Instalar o APK nos celulares (HTTPS; `usesCleartextTraffic` fica inofensivo).

## Parte 5 — Teste final

No celular em **dados móveis**:
1. `https://<dominio>.ngrok-free.app/api/ambientes?ativo=1` → JSON.
2. Abrir o app, selecionar ambiente, medir.

## Limites e observações

- ngrok Free: 1 domínio estático, ~40 conexões/min — ok para TCC.
- Sem autenticação (CORS `*`): qualquer um com a URL pode enviar medições. Opcional depois: token simples.
- `ruido.db` fica no disco do Pi — sobrevive a reinícios.
- Pi precisa ficar ligado para os celulares acessarem.

## Comandos de referência

| Ação | Comando (no Pi) |
|---|---|
| Subir backend manual | `cd backend && source venv/bin/activate && python main.py` |
| Subir túnel manual | `ngrok http 5000 --domain=ruido-tcc.ngrok-free.app` |
| Ver serviços | `systemctl status soundtracker ngrok` |
| Logs | `journalctl -u soundtracker -f` |