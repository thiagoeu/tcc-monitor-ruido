# Firmware ESP32 - Monitor de Ruído

Este diretório contém o firmware embarcado para o ESP32 que realiza a leitura de um microfone I2S, calcula os decibéis e envia para o backend via requisição HTTP POST.

## Pinagem (Wiring)

Conecte os pinos do seu microfone I2S aos seguintes pinos do ESP32:

* **I2S_SCK (BCLK):** GPIO 18
* **I2S_WS (LRC):** GPIO 19
* **I2S_SD (DOUT):** GPIO 21

## Como configurar

O projeto não deve conter credenciais Wi-Fi hardcoded nos commits. 

1. Copie o arquivo `main/config.example.h` e renomeie para `main/config.h`.
2. Edite o `main/config.h` e coloque o SSID e Senha da sua rede Wi-Fi, além do IP do servidor backend.
3. O `config.h` já está ignorado no `.gitignore`.

## Como compilar e gravar (Build & Flash)

Este firmware foi construído usando o **ESP-IDF**. Se você for utilizar a extensão do ESP-IDF no VS Code:

1. Abra a pasta `code/hardware/esp32_firmware` no VS Code.
2. Defina o target para o seu dispositivo (ex: `esp32`).
3. Dê Build, Flash e Monitor para verificar o funcionamento.

## Calibração

O código usa uma base logarítmica com a adição de um offset (+80.0 dB) estipulado para aproximar o valor ao de um decibelímetro real. Você deve ajustar essa constante no arquivo `esp_main.c` dependendo da sensibilidade real do seu microfone (ex: INMP441, SPH0645).
