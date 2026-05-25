from pathlib import Path
from threading import Lock

from ..database import (
    get_connection,
    row_to_dict,
    utc_now_iso,
)

SERIAL_SCAN_AVAILABLE = False
try:
    import serial
    import serial.tools.list_ports
    import minimalmodbus

    SERIAL_SCAN_AVAILABLE = True
except ImportError:
    pass


SERIAL_SCAN_LOCK = Lock()

def get_monitoramento(limit):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM ambientes ORDER BY id ASC")
    ambientes = [row_to_dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT m.id, m.ambiente_id, a.nome AS ambiente_nome, a.sensor_id,
               a.limite_db, m.db, m.excedeu_limite, m.created_at
        FROM medicoes m
        JOIN ambientes a ON a.id = m.ambiente_id
        ORDER BY m.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    medicoes = [row_to_dict(row) for row in cursor.fetchall()]

    latest_by_ambiente = {}
    for medicao in medicoes:
        if medicao["ambiente_id"] not in latest_by_ambiente:
            latest_by_ambiente[medicao["ambiente_id"]] = medicao

    cursor.execute(
        """
        SELECT al.id, al.ambiente_id, al.medicao_id, al.mensagem, al.created_at,
               a.nome AS ambiente_nome
        FROM alertas al
        JOIN ambientes a ON a.id = al.ambiente_id
        ORDER BY al.id DESC
        LIMIT 20
        """
    )
    alertas = [row_to_dict(row) for row in cursor.fetchall()]

    connection.close()

    return {
        "ambientes": ambientes,
        "ultima_por_ambiente": latest_by_ambiente,
        "medicoes": medicoes,
        "alertas": alertas,
        "servidor_em": utc_now_iso(),
    }


def _list_serial_ports():
    ports = []
    found = set()

    for info in serial.tools.list_ports.comports():
        found.add(info.device)
        ports.append(
            {
                "device": info.device,
                "description": info.description,
            }
        )

    for raw in ("/dev/ttyAMA0", "/dev/ttyAMA1", "/dev/ttyS0", "/dev/serial0"):
        if Path(raw).exists() and raw not in found:
            ports.append(
                {
                    "device": raw,
                    "description": "Detectada no filesystem",
                }
            )
            found.add(raw)

    return ports


def _probe_modbus_id(port, slave_addr, baudrate, timeout, registers, function_code):
    try:
        instrument = minimalmodbus.Instrument(port, slave_addr)
        instrument.serial.baudrate = baudrate
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = timeout
        instrument.mode = minimalmodbus.MODE_RTU
        instrument.close_port_after_each_call = True
    except (serial.SerialException, OSError, ValueError) as exc:
        raise RuntimeError(
            f"Nao foi possivel abrir a porta serial '{port}': {exc}"
        ) from exc

    for register in registers:
        try:
            value = instrument.read_register(
                register,
                number_of_decimals=0,
                functioncode=function_code,
                signed=False,
            )
            return {
                "id_modbus": slave_addr,
                "register": register,
                "raw_value": value,
            }
        except (
            minimalmodbus.ModbusException,
            serial.SerialException,
            ValueError,
            TypeError,
            OSError,
            AttributeError,
        ):
            continue

    return None


def scan_sensores_fisicos(
    port,
    baudrate,
    start_id,
    end_id,
    registers,
    function_code,
    timeout,
):
    if not SERIAL_SCAN_AVAILABLE:
        raise RuntimeError(
            "Dependências de serial ausentes no backend. Instale minimalmodbus e pyserial."
        )

    if start_id < 1 or end_id > 247 or start_id > end_id:
        raise ValueError("Faixa de IDs inválida. Use 1..247 e start_id <= end_id.")

    if function_code not in (3, 4):
        raise ValueError("function_code deve ser 3 ou 4.")

    if not registers:
        raise ValueError("Informe ao menos um registrador para teste.")

    portas = _list_serial_ports()
    portas_disponiveis = {item["device"] for item in portas}

    if port not in portas_disponiveis:
        if portas_disponiveis:
            sugestoes = ", ".join(sorted(portas_disponiveis))
            raise ValueError(
                f"Porta serial '{port}' nao encontrada. Portas detectadas: {sugestoes}"
            )
        raise ValueError(
            f"Porta serial '{port}' nao encontrada e nenhuma porta serial foi detectada."
        )

    encontrados = []

    # Evita leituras concorrentes da mesma UART quando houver multiplas requisicoes.
    with SERIAL_SCAN_LOCK:
        for slave_addr in range(start_id, end_id + 1):
            try:
                found = _probe_modbus_id(
                    port,
                    slave_addr,
                    baudrate,
                    timeout,
                    registers,
                    function_code,
                )
            except RuntimeError as exc:
                raise ValueError(str(exc)) from exc
            if found:
                encontrados.append(found)

    return {
        "porta": port,
        "baudrate": baudrate,
        "start_id": start_id,
        "end_id": end_id,
        "registers": registers,
        "function_code": function_code,
        "timeout": timeout,
        "portas_detectadas": portas,
        "sensores": encontrados,
        "total_encontrados": len(encontrados),
        "escaneado_em": utc_now_iso(),
    }
