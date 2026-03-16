import argparse
import random
import time

import requests


def parse_sensors(raw_sensors):
    sensors = []
    for item in raw_sensors.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 3:
            raise ValueError(
                "Formato inválido em --sensors. Use: sensorA:40:85,sensorB:45:90"
            )
        sensor_id, minimum, maximum = parts
        min_db = float(minimum)
        max_db = float(maximum)
        if min_db >= max_db:
            raise ValueError(f"Faixa inválida para {sensor_id}: min precisa ser < max")
        sensors.append({"sensor_id": sensor_id, "min_db": min_db, "max_db": max_db})

    if not sensors:
        raise ValueError("Nenhum sensor configurado.")
    return sensors


def generate_db(min_db, max_db):
    base = random.uniform(min_db, max_db)
    if random.random() < 0.12:
        base += random.uniform(5, 12)
    return round(base, 2)


def send_measurement(api_url, payload, timeout=4):
    response = requests.post(api_url, json=payload, timeout=timeout)
    if response.status_code >= 400:
        body = response.text[:200]
        raise RuntimeError(f"API retornou {response.status_code}: {body}")
    return response.json()


def run(api_url, sensors, interval_seconds):
    print(f"Iniciando mock: {len(sensors)} sensor(es), intervalo={interval_seconds}s")
    print(f"Enviando para: {api_url}")

    while True:
        for sensor in sensors:
            db = generate_db(sensor["min_db"], sensor["max_db"])
            payload = {"sensor_id": sensor["sensor_id"], "db": db}
            try:
                result = send_measurement(api_url, payload)
                status = "ALERTA" if result.get("excedeu_limite") else "OK"
                print(f"[{sensor['sensor_id']}] {db:.1f} dB -> {status}")
            except Exception as error:
                print(f"[{sensor['sensor_id']}] erro ao enviar: {error}")

        time.sleep(interval_seconds)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Mock de sensores E06A para testes do backend no Raspberry Pi"
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:5000/api/medicoes",
        help="Endpoint da API para ingestão de medições",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Intervalo entre ciclos de envio, em segundos",
    )
    parser.add_argument(
        "--sensors",
        default="e06a-001:45:80,e06a-002:35:75",
        help="Lista de sensores no formato sensor:min:max separados por vírgula",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    configured_sensors = parse_sensors(args.sensors)
    run(args.api_url, configured_sensors, max(args.interval, 1.0))