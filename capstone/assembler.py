#!/usr/bin/env python3
"""Two-pass Hack assembler for the Nand2Tetris capstone (K=51)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
}
PREDEFINED.update({f"R{i}": i for i in range(16)})

DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}
JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}
COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "M": "1110000",
    "!D": "0001101", "!A": "0110001", "!M": "1110001",
    "-D": "0001111", "-A": "0110011", "-M": "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101",
}
COMMUTATIVE = {
    "A+D": "D+A", "M+D": "D+M",
    "A&D": "D&A", "M&D": "D&M",
    "A|D": "D|A", "M|D": "D|M",
}
SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")


def clean_source(path: Path):
    """Return (original_line_number, cleaned_instruction) pairs."""
    result = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.split("//", 1)[0].strip()
        if line:
            result.append((line_number, re.sub(r"\s+", "", line)))
    return result


def first_pass(lines):
    symbols = dict(PREDEFINED)
    labels = {}
    rom_address = 0

    for line_number, line in lines:
        if line.startswith("("):
            if not line.endswith(")") or line.count("(") != 1 or line.count(")") != 1:
                raise ValueError(f"Line {line_number}: malformed label declaration")
            label = line[1:-1]
            if not SYMBOL_RE.fullmatch(label):
                raise ValueError(f"Line {line_number}: invalid label name '{label}'")

            if label in symbols:
                # K=51 -> K mod 3 = 0: warn on duplicate labels.
                print(
                    f"Warning: Line {line_number}: duplicate label '{label}' "
                    f"(first definition/address {symbols[label]} retained)",
                    file=sys.stderr,
                )
            else:
                symbols[label] = rom_address
                labels[label] = rom_address
        else:
            rom_address += 1

    if rom_address > 32768:
        raise ValueError("Program exceeds the 32K instruction ROM limit")

    return symbols, labels


def parse_c_instruction(line: str, line_number: int) -> str:
    if line.count("=") > 1 or line.count(";") > 1:
        raise ValueError(f"Line {line_number}: malformed C-instruction '{line}'")

    if "=" in line:
        dest, remainder = line.split("=", 1)
    else:
        dest, remainder = "", line

    if ";" in remainder:
        comp, jump = remainder.split(";", 1)
    else:
        comp, jump = remainder, ""

    comp = COMMUTATIVE.get(comp, comp)

    if dest not in DEST:
        raise ValueError(f"Line {line_number}: invalid destination '{dest}'")
    if comp not in COMP:
        raise ValueError(f"Line {line_number}: invalid computation '{comp}'")
    if jump not in JUMP:
        raise ValueError(f"Line {line_number}: invalid jump '{jump}'")

    return "111" + COMP[comp] + DEST[dest] + JUMP[jump]


def assemble(source: Path, output: Path) -> None:
    lines = clean_source(source)
    symbols, labels = first_pass(lines)
    variables = {}
    next_variable = 16
    machine_code = []

    for line_number, line in lines:
        if line.startswith("("):
            continue

        if line.startswith("@"):
            token = line[1:]
            if not token:
                raise ValueError(f"Line {line_number}: empty A-instruction")

            if token.isdecimal():
                address = int(token)
            else:
                if not SYMBOL_RE.fullmatch(token):
                    raise ValueError(f"Line {line_number}: invalid symbol '{token}'")
                if token not in symbols:
                    if next_variable > 16383:
                        raise ValueError(f"Line {line_number}: variable RAM space exhausted")
                    symbols[token] = next_variable
                    variables[token] = next_variable
                    next_variable += 1
                address = symbols[token]

            if not 0 <= address <= 32767:
                raise ValueError(f"Line {line_number}: A-instruction value out of range: {address}")
            machine_code.append(f"{address:016b}")
        else:
            machine_code.append(parse_c_instruction(line, line_number))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(machine_code) + "\n", encoding="ascii")

    # Required K=51 feature: export every user-defined label and variable.
    symbol_file = source.with_name("symbols.txt")
    with symbol_file.open("w", encoding="utf-8") as stream:
        stream.write("# Hack assembler symbols (K=51)\n")
        stream.write("# Name\tAddress\tType\n")
        for name, address in sorted(labels.items(), key=lambda item: (item[1], item[0])):
            stream.write(f"{name}\t{address}\tLABEL\n")
        for name, address in sorted(variables.items(), key=lambda item: item[1]):
            stream.write(f"{name}\t{address}\tVARIABLE\n")

    print(f"Assembled {source} -> {output}")
    print(f"Instructions: {len(machine_code)}")
    print(f"Labels: {len(labels)} | Variables: {len(variables)}")
    print(f"Symbol table: {symbol_file}")


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python assembler.py input.asm [output.hack]")
        raise SystemExit(2)

    source = Path(sys.argv[1]).resolve()
    if not source.is_file():
        raise SystemExit(f"Input file not found: {source}")

    output = Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else source.with_suffix(".hack")

    try:
        assemble(source, output)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))


if __name__ == "__main__":
    main()