import argparse
import subprocess
import time
import math
import requests
import numpy as np

def send_measurement(api_url, sensor_id, db_value, timeout=4):
    """Envia o valor calculado para a API local."""
    payload = {"sensor_id": sensor_id, "db": db_value}
    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
        if response.status_code >= 400:
            print(f"[{sensor_id}] Erro da API ({response.status_code}): {response.text[:100]}")
        else:
            result = response.json()
            status = "ALERTA" if result.get("excedeu_limite") else "OK"
            print(f"[{sensor_id}] {db_value:.1f} dB -> {status}")
    except Exception as error:
        print(f"[{sensor_id}] Falha ao enviar para {api_url}: {error}")

def run(api_url, sensor_id, device="hw:1,0", interval_seconds=0.5):
    """
    Inicia a escuta do microfone usando 'arecord' (via subprocess).
    """
    RATE = 48000
    CHANNELS = 2
    
    # Define o tamanho do bloco de áudio lido com base no intervalo desejado
    # Ex: 0.5s = RATE // 2, 2.0s = RATE * 2
    BLOCK = int(RATE * interval_seconds)

    print(f"Iniciando captura com arecord ({device}) para o sensor '{sensor_id}'...")
    print(f"Intervalo de envio: {interval_seconds}s")

    proc = subprocess.Popen(
        [
            "arecord",
            "-D", device,
            "-f", "S32_LE",
            "-r", str(RATE),
            "-c", str(CHANNELS),
            "-t", "raw",
            "-q"
        ],
        stdout=subprocess.PIPE
    )

    try:
        while True:
            # Lemos os bytes brutos: BLOCK * Canais * 4 bytes (S32_LE = 32 bits = 4 bytes)
            raw = proc.stdout.read(BLOCK * CHANNELS * 4)

            if len(raw) == 0:
                print("Fluxo de áudio vazio. Encerrando...")
                break

            samples = np.frombuffer(raw, dtype=np.int32)

            # O INMP441 com L/R no GND envia dados para o canal esquerdo (índices pares)
            left = samples[::2].astype(np.float64)

            # Calcula o RMS
            rms = np.sqrt(np.mean(left ** 2))

            if rms < 1:
                db_fs = -100.0
            else:
                # 2147483647.0 é o valor máximo positivo para um inteiro de 32 bits assinado (S32_LE)
                db_fs = 20 * math.log10(rms / 2147483647.0)

            # Converte dBFS (-100 ~ 0) para dB SPL positivo aproximado (0 ~ 100)
            db_spl = max(0.0, min(100.0, db_fs + 100.0))
            
            # Envia para a API
            send_measurement(api_url, sensor_id, round(db_spl, 2))

    except KeyboardInterrupt:
        print("\nCaptura encerrada pelo usuário.")
    except Exception as e:
        print(f"Erro fatal de áudio: {e}")
    finally:
        proc.terminate()

def build_parser():
    parser = argparse.ArgumentParser(
        description="Leitor de microfone I2S (INMP441) via arecord para Raspberry Pi"
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:5000/api/medicoes",
        help="Endpoint da API para ingestão de medições",
    )
    parser.add_argument(
        "--sensor",
        default="e06a-001",
        help="ID do sensor que aparecerá no sistema",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Intervalo de cálculo/envio em segundos (ex: 0.5 = 2 vezes/s)",
    )
    parser.add_argument(
        "--device",
        default="hw:1,0",
        help="Dispositivo ALSA para o arecord (padrão: hw:1,0)",
    )
    return parser

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    
    run(
        api_url=args.api_url,
        sensor_id=args.sensor,
        device=args.device,
        interval_seconds=max(args.interval, 0.1)
    )
