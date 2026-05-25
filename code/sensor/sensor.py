import argparse
import random
import sys
import time
from datetime import datetime
import requests

# Tentativa de importação das dependências físicas
SERIAL_AVAILABLE = False
try:
    import serial
    import minimalmodbus
    SERIAL_AVAILABLE = True
except ImportError:
    pass


def log_info(sensor_id, msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{sensor_id}] INFO: {msg}", flush=True)


def log_warn(sensor_id, msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{sensor_id}] ⚠️ AVISO: {msg}", sys.stderr, flush=True)


def log_error(sensor_id, msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{sensor_id}] ❌ ERRO: {msg}", sys.stderr, flush=True)


def send_to_backend(api_url, sensor_id, db_value, timeout=3.0):
    """Envia a leitura de ruído para o backend via HTTP POST."""
    payload = {"sensor_id": sensor_id, "db": db_value}
    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            status = "ALERTA 🚨" if result.get("excedeu_limite") else "OK"
            return f"Enviado com sucesso -> {db_value:.1f} dB ({status})"
        elif response.status_code == 404:
            return f"Aviso do Backend: Sensor ID '{sensor_id}' não está cadastrado ou ativo no banco de dados."
        else:
            return f"Erro HTTP {response.status_code}: {response.text[:150]}"
    except requests.RequestException as e:
        raise RuntimeError(f"Indisponibilidade de rede/API: {e}")


def init_modbus_sensor(port, slave_addr, baudrate):
    """Inicializa e configura o instrumento Modbus RTU."""
    if not SERIAL_AVAILABLE:
        raise ImportError(
            "As bibliotecas 'minimalmodbus' e 'pyserial' são necessárias para o sensor físico.\n"
            "Instale-as executando: pip install minimalmodbus pyserial"
        )
    
    instrument = minimalmodbus.Instrument(port, slave_addr)
    instrument.serial.baudrate = baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 1.0
    instrument.mode = minimalmodbus.MODE_RTU
    
    # Não fechar a porta serial após cada transação para melhor performance
    instrument.close_port_after_each_call = False
    return instrument


def read_from_hardware(instrument, register):
    """Lê do hardware utilizando Modbus RTU. 
    
    Por padrão, a biblioteca minimalmodbus divide por 10 se informarmos number_of_decimals=1,
    já que os sensores ZTS-ZS-BZ transmitem com 1 casa decimal (ex: 452 -> 45.2 dB).
    """
    try:
        # Usa código de função 3 (Read Holding Registers) para ler o registrador de ruído
        val = instrument.read_register(register, number_of_decimals=1, functioncode=3)
        return float(val)
    except (minimalmodbus.ModbusException, serial.SerialException) as e:
        raise RuntimeError(f"Falha de hardware/serial: {e}")


def run_sensor_client(args):
    sensor_id = args.sensor_id
    api_url = args.api_url
    interval = max(0.5, args.interval)
    
    # Determinação do modo de execução (Real vs Simulação)
    sim_mode = args.debug_sim
    if not SERIAL_AVAILABLE:
        if not sim_mode:
            log_warn(
                sensor_id, 
                "Dependências de hardware ausentes. Ativando modo de simulação física (--debug-sim) automaticamente."
            )
            sim_mode = True
    
    if sim_mode:
        log_info(sensor_id, "=== INICIANDO CLIENTE NO MODO SIMULAÇÃO DE HARDWARE ===")
        log_info(sensor_id, f"Mockando dados físicos para ID '{sensor_id}' e enviando para '{api_url}'")
    else:
        log_info(sensor_id, "=== INICIANDO CLIENTE NO MODO PRODUÇÃO DE HARDWARE ===")
        log_info(sensor_id, f"Lendo sensor físico em '{args.port}' (Baudrate: {args.baudrate}, Modbus Address: {args.slave_addr})")
        log_info(sensor_id, f"Enviando dados para '{api_url}' a cada {interval} segundos")
        
        try:
            instrument = init_modbus_sensor(args.port, args.slave_addr, args.baudrate)
            log_info(sensor_id, "✓ Conexão serial com o instrumento Modbus RTU inicializada com sucesso!")
        except Exception as e:
            log_error(sensor_id, f"Falha crítica na inicialização da porta serial: {e}")
            log_warn(sensor_id, "O script irá tentar inicializar novamente em 5 segundos...")
            time.sleep(5)
            # Tenta novamente iniciando do zero
            sys.exit(1)

    while True:
        try:
            if sim_mode:
                # Gera um ruído aleatório realista na faixa de 40.0 a 80.0 dB
                # com pequenos picos ocasionais
                base = random.uniform(42.0, 68.0)
                if random.random() < 0.15:
                    base += random.uniform(5.0, 15.0)
                db_value = round(base, 1)
            else:
                db_value = read_from_hardware(instrument, args.register)
                
            # Envia para a API REST local
            result_msg = send_to_backend(api_url, sensor_id, db_value)
            log_info(sensor_id, f"Leitura: {db_value:.1f} dBA | {result_msg}")
            
        except RuntimeError as e:
            # Captura falhas de hardware ou indisponibilidade de rede
            log_error(sensor_id, str(e))
        except Exception as e:
            # Captura qualquer outro erro inesperado para evitar que o daemon quebre
            log_error(sensor_id, f"Erro inesperado no loop principal: {e}")
            
        time.sleep(interval)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Leitor de Sensor de Ruído Físico Modbus RTU via GPIO UART"
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:5000/api/medicoes",
        help="Endpoint de ingestão de medições do backend Flask (padrão: http://127.0.0.1:5000/api/medicoes)",
    )
    parser.add_argument(
        "--port",
        default="/dev/serial0",
        help="Porta serial física onde o sensor está conectado (padrão: /dev/serial0)",
    )
    parser.add_argument(
        "--sensor-id",
        default="e06a-001",
        help="Código identificador do sensor associado no backend (padrão: e06a-001)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Intervalo de leitura e envio de dados em segundos (padrão: 2.0)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Taxa de comunicação baudrate serial do sensor (padrão: 9600)",
    )
    parser.add_argument(
        "--slave-addr",
        type=int,
        default=1,
        help="ID de escravo Modbus do sensor (padrão: 1)",
    )
    parser.add_argument(
        "--register",
        type=int,
        default=0,
        help="Endereço decimal do registrador Modbus que guarda o valor de ruído (padrão: 0)",
    )
    parser.add_argument(
        "--debug-sim",
        action="store_true",
        help="Modo simulação: gera dados de ruído virtuais sem acessar a porta serial",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        run_sensor_client(args)
    except KeyboardInterrupt:
        print("\nCliente de sensor finalizado manualmente pelo usuário.")
        sys.exit(0)
