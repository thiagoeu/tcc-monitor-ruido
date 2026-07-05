# 🎵 SoundTracker - Monitor de Decibéis

Aplicativo mobile desenvolvido em React Native com Expo para medição de níveis sonoros em tempo real utilizando o microfone do dispositivo.

---

## 📋 Índice

1. Sobre o Projeto
2. Funcionalidades
3. Tecnologias Utilizadas
4. Arquitetura do Projeto
5. Como Executar
6. Configuração da API
7. Fluxo de Medição
8. Interface do Usuário
9. Limitações e Considerações
   {10. Licença}

---

## 📱 Sobre o Projeto

O SoundTracker é um decibelímetro mobile que utiliza o microfone do dispositivo para capturar níveis sonoros em tempo real. Desenvolvido para aplicações de monitoramento ambiental, o app apresenta uma interface limpa e intuitiva, com feedback visual imediato.

### Objetivos

- Monitoramento contínuo de ruído ambiente
- Visualização em tempo real de níveis sonoros
- Registro de métricas (mínimo, médio e máximo)
- Integração com API para armazenamento de dados

---

## ✨ Funcionalidades

| Funcionalidade           | Descrição                                      |
| ------------------------ | ---------------------------------------------- |
| 🎤 Medição em Tempo Real | Captura contínua do nível sonoro do ambiente   |
| 📊 Display de dB         | Exibição numérica atualizada 150ms             |
| 📈 Indicadores Visuais   | Barra de progresso e cores dinâmicas por nível |
| 📉 Estatísticas          | Mínimo, média e máximo da sessão atual         |
| 🔄 Seleção de Ambientes  | Escolha entre diferentes locais de medição     |
| 🔒 Controle de Sessão    | Prevenção de múltiplas medições no mesmo local |
| 📡 Integração API        | Envio de dados para servidor                   |
| ⏱️ Heartbeat             | Manutenção de sessão ativa                     |

---

## 🛠️ Tecnologias Utilizadas

### Frontend

- React Native (0.81.5) - Framework mobile
- Expo (54.0.33) - Plataforma de desenvolvimento
- expo-av (16.0.8) - Captura e processamento de áudio
- expo-constants (18.0.13) - Configurações do app

### Linguagem

- JavaScript (ES6+)
- React Hooks

---

## 🏗️ Arquitetura do Projeto

### Estrutura de Pastas

```bash
soundtracker/
├── src/
│   ├── components/
│   │   ├── ControlButton.js       # Botão iniciar/parar
│   │   ├── MeterBar.js            # Barra de progresso
│   │   ├── MeterDisplay.js        # Display principal
│   │   ├── NoiseStatus.js         # Status de ruído
│   │   ├── SensorSelector.js      # Seleção de ambiente
│   │   └── StatsPanel.js          # Estatísticas
│   ├── hooks/
│   │   └── useDecibelMeter.js     # Lógica principal
│   ├── services/
│   │   └── api.js                 # Integração com API
│   └── shared/
│       └── soundUtils.js          # Funções de formatação
├── App.js                         # Ponto de entrada
├── app.config.js                  # Configuração do Expo
├── package.json                   # Dependências
└── readme.md                      # Documentação
```

### Principais Componentes

#### useDecibelMeter (Hook Principal)

- Gerencia o ciclo de vida da captura de áudio
- Controla estados de medição
- Processa dados do microfone
- Gerencia comunicação com API

```javascript
const { db, isRecording, minDb, maxDb, avgDb, start, stop } =
  useDecibelMeter(sensorId);
```

#### SensorSelector (Seleção de Ambiente)

- Lista ambientes disponíveis
- Gerencia estado de ocupação
- Feedback visual para ambientes em uso

#### StatsPanel (Painel de Estatísticas)

- Exibe mínimo, média e máximo da sessão
- Atualização em tempo real

---

## 🚀 Como Executar

### Pré-requisitos

- Node.js (versão 16 ou superior)
- Expo CLI
- Smartphone com Expo Go ou emulador

### Passo a Passo

1. Clone o repositório
   git clone https://github.com/seu-usuario/soundtracker.git
   cd soundtracker

2. Instale as dependências
   npm install

3. Configure as variáveis de ambiente

   # Crie um arquivo .env na raiz do projeto

   API_BASE_URL=http://seu-servidor:5000/api

4. Execute o projeto
   `npx expo start`

5. Teste no dispositivo
   - Android: Instale o Expo Go e escaneie o QR Code
   - iOS: Use a câmera do iPhone para escanear (direto no aplicativo de câmera)
   - Emulador: Use npx expo start --android ou --ios

---

## 🔧 Configuração da API

### Variáveis de Ambiente

| Variável     | Descrição       | Exemplo                       |
| ------------ | --------------- | ----------------------------- |
| API_BASE_URL | URL base da API | http://192.168.1.100:5000/api |

### Endpoints Utilizados

| Endpoint                           | Método | Descrição                   |
| ---------------------------------- | ------ | --------------------------- |
| /api/ambientes?ativo=1             | GET    | Lista ambientes disponíveis |
| /api/medicoes                      | POST   | Envia medição               |
| /api/sessoes                       | POST   | Inicia sessão de medição    |
| /api/sessoes/{sensor_id}           | DELETE | Finaliza sessão             |
| /api/sessoes/{sensor_id}/heartbeat | PUT    | Mantém sessão ativa         |

### Exemplo de Configuração

```javascript
// app.config.js
extra: {
  apiBaseUrl: process.env.API_BASE_URL || "http://localhost:5000/api",
}
```

---

## 🔄 Fluxo de Medição

### Captura de Áudio

### Captura de Áudio

**1. Solicitação de permissão**

```javascript
const { granted } = await Audio.requestPermissionsAsync();
```

**2. Configuração de áudio**

```javascript
await Audio.setAudioModeAsync({
  allowsRecordingIOS: true,
  playsInSilentModeIOS: true,
});
```

**3. Início da gravação**

```javascript
const { recording } = await Audio.Recording.createAsync(
  Audio.RecordingOptionsPresets.HIGH_QUALITY,
  undefined,
  true,
);
```

### Processamento de Dados

| Etapa      | Descrição                       | Frequência     |
| ---------- | ------------------------------- | -------------- |
| Leitura    | Captura metering do microfone   | 150ms          |
| Suavização | Filtro exponencial (70/30)      | A cada leitura |
| Conversão  | Mapeamento para dB SPL (35-100) | A cada leitura |
| Envio      | Upload para API                 | 2s             |
| Heartbeat  | Manutenção de sessão            | 10s            |

### Gerenciamento de Sessão

1. Selecionar Ambiente
2. Ocupar Ambiente
3. Iniciar Medição
4. Coletar Dados (Loop a cada 2s)
5. Enviar Medição (Loop a cada 2s)
6. Parar Medição
7. Liberar Ambiente

---

## 🎨 Interface do Usuário

### Componentes Visuais

| Componente     | Função              | Cores                             |
| -------------- | ------------------- | --------------------------------- |
| MeterDisplay   | Exibe dB atual      | Dinâmica (verde→amarelo→vermelho) |
| MeterBar       | Barra de progresso  | Dinâmica                          |
| NoiseStatus    | Texto descritivo    | Dinâmica                          |
| StatsPanel     | Mín/Méd/Máx         | Branco fixo                       |
| ControlButton  | Iniciar/Parar       | Verde / Vermelho                  |
| SensorSelector | Seleção de ambiente | Roxo (#7C6FF7)                    |

### Escala de Cores

| Faixa (dB) | Cor         | Status              |
| ---------- | ----------- | ------------------- |
| 0 - 50     | 🟢 Verde    | Silencioso/Moderado |
| 50 - 75    | 🟡 Amarelo  | Alto                |
| 75+        | 🔴 Vermelho | Perigoso            |

---

## ⚠️ Limitações e Considerações

### Precisão da Medição

- Microfone: A precisão varia conforme o modelo do dispositivo
- Escala: Os valores são aproximações da escala dB SPL
- AGC: Controle automático de ganho pode afetar leituras
- Hardware: Não substitui equipamentos profissionais

### Recomendações

- Utilize em ambiente controlado para melhor precisão
- Mantenha o microfone desobstruído
- Evite vento e ruídos abruptos
- Compare com equipamento calibrado para validação

### Performance

- O app processa ~6.7 leituras por segundo
- Consumo de bateria moderado
- Uso otimizado de memória

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga os passos:

1. Faça um Fork do projeto
2. Crie uma Branch (git checkout -b feature/nova-funcionalidade)
3. Commit suas mudanças (git commit -m 'Adiciona nova funcionalidade')
4. Push para a Branch (git push origin feature/nova-funcionalidade)
5. Abra um Pull Request

---

## 📧 Contato

- Autor: Thiago Barbosa de Aráujo
- GitHub: @thiagoeu
