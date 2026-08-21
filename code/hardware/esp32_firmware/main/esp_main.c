#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "driver/i2s_std.h"
#include "esp_http_client.h"

// ==========================================
// CONFIGURAÇÕES DE REDE E BACKEND
// ==========================================
#include "config.h"

#define MAXIMUM_RETRY  5

// ==========================================
// CONFIGURAÇÕES DO I2S
// ==========================================
#define I2S_SCK GPIO_NUM_18
#define I2S_WS  GPIO_NUM_19
#define I2S_SD  GPIO_NUM_21
#define SAMPLE_RATE 44100

static int s_retry_num = 0;
static const char *TAG = "NOISE_RADAR";

// ==========================================
// FUNÇÕES DE EVENTO WI-FI
// ==========================================
static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < MAXIMUM_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "Tentando reconectar ao Wi-Fi...");
        } else {
            ESP_LOGE(TAG, "Falha ao conectar ao Wi-Fi.");
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Conectado! IP: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
    }
}

void wifi_init_sta(void) {
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Wi-Fi configurado. Iniciando conexão...");
}

// ==========================================
// FUNÇÃO DE ENVIO HTTP POST
// ==========================================
void enviar_medicao_para_backend(float decibeis) {
    char json_payload[100];
    snprintf(json_payload, sizeof(json_payload), "{\"sensor_id\": \"esp32-mic-01\", \"db\": %.1f}", decibeis);

    esp_http_client_config_t config = {
        .url = BACKEND_URL,
        .method = HTTP_METHOD_POST,
    };
    
    esp_http_client_handle_t client = esp_http_client_init(&config);
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_post_field(client, json_payload, strlen(json_payload));

    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Enviado: %.1f dB | Status: %d", decibeis, esp_http_client_get_status_code(client));
    } else {
        ESP_LOGE(TAG, "Erro HTTP: %s", esp_err_to_name(err));
    }
    esp_http_client_cleanup(client);
}

// ==========================================
// PROGRAMA PRINCIPAL
// ==========================================
void app_main(void) {
    // 1. Inicializa a memória flash (necessário para o Wi-Fi salvar calibrações)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 2. Inicializa o Wi-Fi
    wifi_init_sta();

    // 3. Aguarda alguns segundos para o Wi-Fi conectar antes de iniciar o áudio
    vTaskDelay(pdMS_TO_TICKS(5000));

    // 4. Inicializa o microfone I2S
    i2s_chan_handle_t rx_handle = NULL;
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO, I2S_ROLE_MASTER);
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, NULL, &rx_handle));

    i2s_std_config_t std_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = I2S_SCK,
            .ws   = I2S_WS,
            .dout = I2S_GPIO_UNUSED,
            .din  = I2S_SD,
            .invert_flags = {
                .mclk_inv = false, .bclk_inv = false, .ws_inv = false,
            },
        },
    };

    ESP_ERROR_CHECK(i2s_channel_init_std_mode(rx_handle, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(rx_handle));

    ESP_LOGI(TAG, "Microfone I2S pronto. Medindo e enviando a cada 2.0s...");

    int16_t sample = 0;
    size_t bytes_read = 0;
    double sum_squares = 0;
    int sample_count = 0;
    
    // Calcula para 2 segundos (tempo padrão do seu sistema Noise Radar)
    const int samples_per_2_seconds = SAMPLE_RATE * 2; 

    while (1) {
        esp_err_t res = i2s_channel_read(rx_handle, &sample, sizeof(sample), &bytes_read, portMAX_DELAY);
        
        if (res == ESP_OK && bytes_read > 0) {
            sum_squares += (double)(sample * sample);
            sample_count++;

            if (sample_count >= samples_per_2_seconds) {
                double rms = sqrt(sum_squares / sample_count);
                
                if (rms > 0) {
                    double dbfs = 20.0 * log10(rms / 32768.0);
                    // Lembre-se de ajustar este offset de 80.0 conforme calibrado com seu decibelímetro
                    double db_estimado = dbfs + 80.0; 
                    
                    enviar_medicao_para_backend((float)db_estimado);
                }

                sum_squares = 0;
                sample_count = 0;
            }
        }
    }
}
