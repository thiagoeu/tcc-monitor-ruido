import argparse
from pathlib import Path

SERIAL_AVAILABLE = False
try:
    import serial
    import serial.tools.list_ports
    import minimalmodbus

    SERIAL_AVAILABLE = True
except ImportError:
    pass


def build_parser():
    parser = argparse.ArgumentParser(
        description="Scanner de IDs Modbus RTU para sensores na serial do Raspberry Pi"
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyAMA0",
        help="Porta serial para varredura (padrao: /dev/ttyAMA0)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Baudrate da serial (padrao: 9600)",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=1,
        help="Primeiro ID Modbus da varredura (padrao: 1)",
    )
    parser.add_argument(
        "--end-id",
        type=int,
        default=32,
        help="Ultimo ID Modbus da varredura (padrao: 32)",
    )
    parser.add_argument(
        "--registers",
        default="0,1",
        help="Lista de registradores separados por virgula para teste (padrao: 0,1)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.25,
        help="Timeout de cada tentativa em segundos (padrao: 0.25)",
    )
    parser.add_argument(
        "--function-code",
        type=int,
        default=3,
        choices=[3, 4],
        help="Function code Modbus (3=holding, 4=input register). Padrao: 3",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="Lista portas seriais detectadas e sai",
    )
    return parser


def parse_registers(value):
    registers = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        registers.append(int(chunk))

    if not registers:
        raise ValueError("Informe ao menos um registrador em --registers")

    return registers


def list_serial_ports():
    print("Portas seriais detectadas:")

    found = set()
    for info in serial.tools.list_ports.comports():
        found.add(info.device)
        print(f"- {info.device} ({info.description})")

    # Inclui portas comuns do Raspberry Pi mesmo quando nao aparecem no list_ports.
    for raw in ("/dev/ttyAMA0", "/dev/ttyAMA1", "/dev/ttyS0", "/dev/serial0"):
        if Path(raw).exists() and raw not in found:
            print(f"- {raw} (detectada no filesystem)")
            found.add(raw)

    if not found:
        print("- Nenhuma porta serial detectada")


def build_instrument(port, slave_addr, baudrate, timeout):
    instrument = minimalmodbus.Instrument(port, slave_addr)
    instrument.serial.baudrate = baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = timeout
    instrument.mode = minimalmodbus.MODE_RTU
    instrument.close_port_after_each_call = True
    return instrument


def probe_slave(port, slave_addr, baudrate, timeout, registers, function_code):
    instrument = build_instrument(port, slave_addr, baudrate, timeout)

    for register in registers:
        try:
            value = instrument.read_register(
                register,
                number_of_decimals=0,
                functioncode=function_code,
                signed=False,
            )
            return True, register, value
        except (minimalmodbus.ModbusException, serial.SerialException, ValueError):
            continue

    return False, None, None


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not SERIAL_AVAILABLE:
        print("Dependencias ausentes. Instale com: pip install minimalmodbus pyserial")
        raise SystemExit(1)

    if args.list_ports:
        list_serial_ports()
        raise SystemExit(0)

    if args.start_id < 1 or args.end_id > 247 or args.start_id > args.end_id:
        print("Faixa de IDs invalida. Use 1..247 e start <= end.")
        raise SystemExit(2)

    registers = parse_registers(args.registers)

    print(f"Varrendo IDs Modbus em {args.port} ({args.baudrate} 8N1)...")
    print(
        f"Faixa: {args.start_id}..{args.end_id} | Function code: {args.function_code} | Registradores: {registers}"
    )

    found = []
    for slave_addr in range(args.start_id, args.end_id + 1):
        ok, register, value = probe_slave(
            args.port,
            slave_addr,
            args.baudrate,
            args.timeout,
            registers,
            args.function_code,
        )
        if ok:
            found.append((slave_addr, register, value))
            print(f"[OK] ID {slave_addr:>3} respondeu no registrador {register} (valor bruto={value})")

    print("\nResumo:")
    if not found:
        print("- Nenhum ID respondeu.")
        print("- Confira porta, baudrate, fiacao TX/RX e endereco de registrador.")
        print("- Se necessario, tente --function-code 4 e outros --registers.")
        return

    ids = ", ".join(str(item[0]) for item in found)
    print(f"- IDs Modbus encontrados: {ids}")
    print("- No dashboard, sensor_id e um codigo textual (ex: sala-ruido-01).")
    print("- No script do sensor, use o ID Modbus encontrado em --slave-addr.")


if __name__ == "__main__":
    main()