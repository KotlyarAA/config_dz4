import argparse
import yaml
import struct

# Constants for command bit masks
COMMAND_MASK = 0b11111  # Маска команды (5 бит)
REGISTER_MASK = 0b111111  # Маска регистра (6 бит)
ADDRESS_MASK = 0xFFFFFFFF  # Маска адреса (32 бита)

# VM Memory
memory = [0] * 1024  # Память виртуальной машины

# Helper to extract fields from instruction
def extract_fields(instruction):
    """Извлечение полей A, B, C из инструкции."""
    print(f"Extracting fields from instruction: 0x{instruction:08X}")
    A = instruction & COMMAND_MASK  # Команда
    B = (instruction >> 5) & REGISTER_MASK  # Регистровое поле
    C = (instruction >> 11)  # Адресное поле
    print(f"Extracted fields -> A: {A}, B: {B}, C: {C}")
    return A, B, C

# Assembler
def assembler(input_file, binary_output, log_output):
    """
    Ассемблер: преобразует текстовые инструкции в бинарные и лог.
    Сохраняет результат в файлы.
    """
    print(f"Starting assembler with input file: {input_file}")
    instructions = []
    log = {}

    # Чтение текстового файла
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        print(f"Read {len(lines)} lines from input file.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Преобразование в бинарные инструкции
    for line_num, line in enumerate(lines):
        if not line.strip():
            print(f"Skipping empty line {line_num + 1}")
            continue  # Пропуск пустых строк
        parts = line.split()
        if len(parts) < 3:
            raise ValueError(f"Invalid instruction format on line {line_num + 1}: '{line}'")
        try:
            command = int(parts[0][2:], 16)  # Код команды (A)
            operand1 = int(parts[1][2:], 16)  # Регистр (B)
            operand2 = int(parts[2][2:], 16)  # Адрес/константа (C)
        except ValueError:
            raise ValueError(f"Invalid hex value on line {line_num + 1}: '{line}'")

        instruction = (operand2 << 11) | (operand1 << 5) | command
        instructions.append(instruction)
        log[f"line_{line_num + 1}"] = f"0x{instruction:08X}"  # Формат "ключ=значение"
        print(f"Line {line_num + 1}: Command {command}, Operand1 {operand1}, Operand2 {operand2} -> Instruction: 0x{instruction:08X}")

    # Сохранение бинарного файла
    with open(binary_output, 'wb') as f:
        for instr in instructions:
            f.write(struct.pack('I', instr))  # Записываем 4 байта на инструкцию
    print(f"Binary instructions written to {binary_output}")

    # Сохранение лога в формате YAML
    with open(log_output, 'w') as f:
        yaml.dump(log, f, default_flow_style=False)
    print(f"Log written to {log_output}")

# Interpreter
def interpreter(binary_input, start_address, end_address, result_output):
    """
    Интерпретатор: выполняет бинарные инструкции.
    Сохраняет результат выполнения в файл YAML.
    """
    print(f"Starting interpreter with binary input: {binary_input}")
    print(f"Start address: {start_address}, End address: {end_address}")
    if not (0 <= start_address < len(memory)) or not (0 <= end_address <= len(memory)):
        raise ValueError(f"Addresses must be in range 0 to {len(memory) - 1}")

    register = [0] * 64  # 64 регистра процессора
    result = {}
    try:
        with open(binary_input, 'rb') as f:
            binary_data = f.read()
        print(f"Read {len(binary_data)} bytes from binary input.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Binary file '{binary_input}' not found.")

    if not binary_data:
        raise ValueError("Binary file is empty!")

    instructions = [struct.unpack('I', binary_data[i:i + 4])[0] for i in range(0, len(binary_data), 4)]
    print(f"Loaded {len(instructions)} instructions from binary file.")

    # Выполнение инструкций
    for instr in instructions:
        A, B, C = extract_fields(instr)  # Извлечение полей команды
        print(f"Executing instruction: A={A}, B={B}, C={C}")
        if A == 6:  # Load constant (загрузка константы)
            register[B] = C
            print(f"Loaded constant {C} into register {B}")
        elif A == 8:  # Read memory (чтение из памяти)
            register[B] = memory[C]
            print(f"Read memory[{C}] -> register[{B}] = {memory[C]}")
        elif A == 25:  # Write memory (запись в память)
            memory[C] = register[B]
            print(f"Wrote register[{B}] -> memory[{C}] = {register[B]}")
        elif A == 10:  # Unary minus (унарный минус)
            register[B] = -memory[C]
            print(f"Unary minus applied: register[{B}] = -memory[{C}] = {-memory[C]}")
        # Запись текущего состояния регистра
        result[f"register_{B}"] = register[B]

    # Сохранение состояния памяти в указанном диапазоне
    result["memory"] = {f"0x{addr:04X}": memory[addr] for addr in range(start_address, end_address)}
    print(f"Memory state saved for addresses {start_address} to {end_address}.")

    # Сохранение результата в формате YAML
    with open(result_output, 'w') as f:
        yaml.dump(result, f, default_flow_style=False)
    print(f"Result written to {result_output}")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Assembler and Interpreter for VM.")
    parser.add_argument('--input', help="Input file for assembler.")
    parser.add_argument('--binary', help="Output binary file.")
    parser.add_argument('--log', help="Log file (YAML) for assembler.")
    parser.add_argument('--start_address', type=int, help="Start address for interpreter.")
    parser.add_argument('--end_address', type=int, help="End address for interpreter.")
    parser.add_argument('--binary_input', help="Binary input file for interpreter.")
    parser.add_argument('--result', help="Result file (YAML) for interpreter.")
    args = parser.parse_args()

    # Выполнение ассемблера
    if args.input and args.binary and args.log:
        print("Assembler step initiated.")
        assembler(args.input, args.binary, args.log)

    # Выполнение интерпретатора
    if args.binary_input and args.start_address is not None and args.end_address is not None and args.result:
        print("Interpreter step initiated.")
        interpreter(args.binary_input, args.start_address, args.end_address, args.result)

    # Ошибка, если ни одна команда не указана
    if not any([args.input, args.binary, args.log, args.binary_input, args.result]):
        print("Error: No valid arguments provided. Use --help for usage information.")

if __name__ == "__main__":
    print("Starting VM assembler and interpreter...")
    main()
