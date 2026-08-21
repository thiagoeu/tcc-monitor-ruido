# Mapeamento de Funcionalidades — App (mobile/App.js)

Visão geral do fluxo do aplicativo decibelímetro, os componentes de UI usados e as chamadas de API/backend por trás de cada funcionalidade.

## Fluxo principal (tela única)

`App.js` é a tela raiz (uma única tela) que orquestra todo o aplicativo. Os estados globais gerenciados no `App`:

| Estado | Tipo | Descrição |
|---|---|---|
| `sensores` | `array` | Lista de ambientes ativos retornados pelo backend |
| `sensorSelecionado` | `object` | Ambiente escolhido pelo usuário (`null` = nenhum) |
| `loadingSensores` | `bool` | Controla o indicador de carregamento do seletor |

O estado de medição (`db`, `minDb`, `maxDb`, `avgDb`, `isRecording`, `start`, `stop`, `ocupacaoError`) vem do hook `useDecibelMeter(sensorId)`, em `src/hooks/useDecibelMeter.js`.

---

## Funcionalidades

### 1. Carregar lista de ambientes/sensores
- **Onde:** `App.js:19-28`
- **Quando:** no mount (`useEffect`) e ao abrir/atualizar o seletor (`onRefresh`).
- **Fluxo:** `carregarSensores()` → `getSensores()` em `src/services/api.js:5` → `GET /api/ambientes?ativo=1`.
- **Saída:** array de ambientes com `{ id, nome, localizacao, sensor_id, limite_db, em_uso, ... }`.

### 2. Selecionar ambiente
- **Onde:** `App.js:52-59` (componente `SensorSelector`)
- **Fluxo:** `onSelect={setSensorSelecionado}` atualiza o estado; `sensorId = sensorSelecionado?.sensor_id` alimenta o hook. O botão de iniciar fica desabilitado (`disabled={!sensorSelecionado}`, `App.js:71`) enquanto nenhum ambiente estiver selecionado.
- O seletor também expõe `onRefresh` (recarregar lista) e recebe `isRecording` para bloquear trocas durante a gravação.

### 3. Iniciar/parar medição de decibéis
- **Onde:** `App.js:69-79` (componente `ControlButton`)
- **Fluxo de iniciar (`start`)** em `useDecibelMeter.js:131-182`:
  1. `ocuparAmbiente(sensorId, DEVICE_ID)` → `POST /api/sessoes` (reserva o ambiente; falha em conflito = ambiente em uso).
  2. `Audio.requestPermissionsAsync()` — permissão de microfone.
  3. `Audio.setAudioModeAsync()` e `Audio.Recording.createAsync()` (gravação com metering).
  4. Inicia 3 loops: **metering** (leitura do microfone a cada 150ms), **envio de medições** (a cada 2s) e **heartbeat** (renovação da sessão a cada 10s).
- **Fluxo de parar (`stop`)** em `useDecibelMeter.js:184-211`:
  1. Limpa todos os intervalos (`metering`, `envio`, `heartbeat`, média).
  2. `stopAndUnloadAsync()` — finaliza a gravação.
  3. Reseta estados (`db=0`, `min/max/avg=null`).
  4. `liberarAmbiente()` → `DELETE /api/sessoes/:sensorId`.

### 4. Captura e processamento de decibéis
- **Onde:** `useDecibelMeter.js:64-111` (intervalo de 150ms)
- Converte o metering do expo-av em dB SPL: `dbSPL = clamp(35, 100, 90 + metering)` (`:75`).
- Suaviza a leitura: `smoothValue = prev * 0.7 + dbSPL * 0.3` (`:77`).
- Atualiza em tempo real o **mínimo**, o **máximo** e acumula valores para **média**.

### 5. Média exibida (por intervalo)
- **Onde:** `useDecibelMeter.js:52-62, 106-110`
- A média exibida é recalculada a cada 2s a partir das leituras do intervalo (`avgTotalRef/avgCountRef`), enquanto a média global (`totalRef/countRef`) fica apenas como referência interna.

### 6. Envio de medições ao backend
- **Onde:** `useDecibelMeter.js:113-120` (intervalo de 2s)
- **Fluxo:** `enviarMedicao(sensorId, db)` → `POST /api/medicoes` com `{ sensor_id, db }` (db arredondado a 2 casas).
- Condição: só envia se `isRecording` e `db > 0`.

### 7. Heartbeat / renovação de sessão
- **Onde:** `useDecibelMeter.js:122-129` (intervalo de 10s)
- **Fluxo:** `heartbeatSessao(sensorId, DEVICE_ID)` → `PUT /api/sessoes/:sensorId/heartbeat` — mantém o ambiente reservado por este dispositivo.

### 8. Tratamento de "Ambiente Ocupado"
- **Onde:** `App.js:36-46`
- Se `ocuparAmbiente` falhar (conflito 409), o hook seta `ocupacaoError`.
- O `App` exibe `Alert.alert("Ambiente Ocupado 🔒", ...)` e recarrega a lista de sensores para refletir o status atualizado (`em_uso`).

### 9. Exibição visual do ruído
- **Onde:** `App.js:61-67`
- `MeterDisplay` — valor numérico atual (dB).
- `NoiseStatus` — rótulo do nível via `getNoiseLabel(db)`.
- `MeterBar` — barra proporcional via `getWidth(db)`.
- **Cores semafóricas** via `getColor(db)` em `src/shared/soundUtils.js`:
  - `< 50` → verde `#00E676`
  - `< 75` → amarelo `#FFD600`
  - `≥ 75` → vermelho `#FF5252`
- **Rótulos de nível:**
  - `< 40` → "Silencioso"
  - `< 60` → "Moderado"
  - `< 80` → "Alto"
  - `≥ 80` → "Perigoso"

### 10. Painel de estatísticas
- **Onde:** `App.js:67` (componente `StatsPanel`)
- Exibe `minDb`, `avgDb` e `maxDb` da sessão atual.

### 11. Limpeza ao desmontar
- **Onde:** `useDecibelMeter.js:213-226` (cleanup do `useEffect`)
- Ao desmontar o componente: limpa todos os intervalos, para a gravação e libera o ambiente, garantindo que nenhuma sessão fique presa.

---

## Identificação do dispositivo

`DEVICE_ID = device-{platform}-{timestamp}-{random}` é gerado no módulo `useDecibelMeter` (`:11`) e usado para reservar/liberar ambientes e renovar a sessão (heartbeat).

## Resumo das chamadas de API

| Ação | Método/Endpoint | Frequência | Local |
|---|---|---|---|
| Listar ambientes | `GET /api/ambientes?ativo=1` | sob demanda | `api.js:5` |
| Reservar ambiente | `POST /api/sessoes` | início da medição | `api.js:47` |
| Enviar medição | `POST /api/medicoes` | a cada 2s | `api.js:19` |
| Heartbeat | `PUT /api/sessoes/:id/heartbeat` | a cada 10s | `api.js:82` |
| Liberar ambiente | `DELETE /api/sessoes/:id` | fim da medição / cleanup | `api.js:64` |

## Componentes de UI

| Componente | Responsabilidade |
|---|---|
| `SensorSelector` | Lista e seleção de ambientes + refresh |
| `MeterDisplay` | Valor numérico do dB atual |
| `NoiseStatus` | Rótulo do nível de ruído |
| `MeterBar` | Barra visual proporcional |
| `StatsPanel` | Estatísticas (min/avg/max) |
| `ControlButton` | Botão iniciar/parar medição |
