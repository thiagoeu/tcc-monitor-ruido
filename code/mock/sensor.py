import argparse
import random
import time

import requests


def parse_sensors(raw_sensors):
    """Parse formato legado: sensor:min:max,sensor2:min2:max2"""
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


def fetch_ambientes_from_api(api_base_url, timeout=4):
    """Busca todos os ambientes (sensores) cadastrados no backend.
    
    Retorna lista de dicts {'sensor_id', 'min_db', 'max_db'}.
    Usa faixa padrão (30-85 dB) para sensores sem limite_db definido.
    """
    try:
        url = f"{api_base_url.replace('/api/medicoes', '')}/api/ambientes"
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            return []
        
        ambientes = response.json()
        sensors = []
        for amb in ambientes:
            sensor_id = amb.get("sensor_id", "")
            if not sensor_id:
                continue
            
            # Use limite_db como referência, com faixa padrão
            limite = amb.get("limite_db", 65)
            min_db = max(30, limite - 20)  # 20 dB abaixo do limite
            max_db = limite + 10  # até 10 dB acima do limite
            
            sensors.append({
                "sensor_id": sensor_id,
                "min_db": min_db,
                "max_db": max_db,
                "ambiente_id": amb.get("id"),
                "nome": amb.get("nome", sensor_id),
            })
        
        return sensors
    except Exception as error:
        print(f"[Aviso] Erro ao buscar ambientes: {error}")
        return []


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


def run(api_url, sensors=None, interval_seconds=5, dynamic=False):
    """Executa o loop de geração de medições.
    
    Args:
        api_url: URL completa do endpoint /api/medicoes
        sensors: Lista inicial de sensores (legado)
        interval_seconds: Intervalo entre ciclos
        dynamic: Se True, busca sensores dinamicamente da API a cada ciclo
    """
    api_base_url = api_url.replace("/api/medicoes", "")
    current_sensors = sensors or []
    last_fetch = 0
    fetch_interval = max(30, interval_seconds * 2)  # Atualiza lista a cada 30s mínimo
    
    print(f"Iniciando mock: intervalo={interval_seconds}s, modo_dinâmico={dynamic}")
    print(f"Enviando para: {api_url}")
    if dynamic:
        print("✓ Modo DINÂMICO ativado: novos sensores serão detectados automaticamente")
    
    cycle = 0
    while True:
        cycle += 1
        current_time = time.time()
        
        # Atualiza lista de sensores dinamicamente a cada 30+ segundos
        if dynamic and (current_time - last_fetch) >= fetch_interval:
            fetched = fetch_ambientes_from_api(api_url)
            if fetched:
                current_sensors = fetched
                last_fetch = current_time
                print(f"[Ciclo {cycle}] ✓ Detectados {len(current_sensors)} sensor(es) do backend")
        
        if not current_sensors:
            print("[Aviso] Nenhum sensor configurado. Aguardando...")
            time.sleep(interval_seconds)
            continue
        
        for sensor in current_sensors:
            db = generate_db(sensor["min_db"], sensor["max_db"])
            payload = {"sensor_id": sensor["sensor_id"], "db": db}
            try:
                result = send_measurement(api_url, payload)
                status = "ALERTA" if result.get("excedeu_limite") else "OK"
                nome = sensor.get("nome", sensor["sensor_id"])
                print(f"[{nome}] {db:.1f} dB @ {sensor['min_db']:.0f}-{sensor['max_db']:.0f} -> {status}")
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
        help="(Obsoleto) Lista de sensores no formato sensor:min:max separados por vírgula",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Modo DINÂMICO: busca sensores do backend automaticamente. Ignora --sensors",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    
    if args.dynamic:
        # Modo dinâmico: ignora --sensors e busca do backend
        run(args.api_url, sensors=None, interval_seconds=max(args.interval, 1.0), dynamic=True)
    else:
        # Modo legado: usa sensores configurados
        configured_sensors = parse_sensors(args.sensors)
        run(args.api_url, sensors=configured_sensors, interval_seconds=max(args.interval, 1.0), dynamic=False)