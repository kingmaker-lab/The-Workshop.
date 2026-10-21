#!/usr/bin/env python3
"""WOLF-VM v0.1 assembler. Only standard library, no macros or file includes."""

import argparse
import re
import struct
from pathlib import Path

OPS = {
    "NOP": (0x00, ""),
    "HALT": (0x01, ""),
    "MOVI": (0x10, "ri"),
    "MOV": (0x11, "rr"),
    "ADD": (0x20, "rr"),
    "SUB": (0x21, "rr"),
    "XOR": (0x22, "rr"),
    "CMP": (0x30, "rr"),
    "JMP": (0x40, "a"),
    "JZ": (0x41, "a"),
    "JNZ": (0x42, "a"),
    "PUSH": (0x50, "r"),
    "POP": (0x51, "r"),
    "CALL": (0x52, "a"),
    "RET": (0x53, ""),
    "LOAD": (0x60, "rm"),
    "STORE": (0x61, "mr"),
}
PATTERN_LABEL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PATTERN_REG = re.compile(r"R([0-7])", re.I)
SIZES = {"r": 1, "i": 4, "a": 4, "m": 2}


def immediate(token, labels, line):
    if token in labels:
        return labels[token]
    try:
        return int(token, 0)
    except ValueError as exc:
        raise ValueError(f"linha {line}: imediato/label invalido: {token}") from exc


def parse_register(token, line):
    match = PATTERN_REG.fullmatch(token)
    if not match:
        raise ValueError(f"linha {line}: registrador deve ser R0..R7: {token}")
    return int(match.group(1))


def assemble(source):
    labels = {}
    instructions = []
    pc = 0
    for line, raw in enumerate(source.splitlines(), start=1):
        code = raw.split(";", 1)[0].split("#", 1)[0].strip()
        if not code:
            continue
        while ":" in code:
            before, after = code.split(":", 1)
            label = before.strip()
            if not PATTERN_LABEL.fullmatch(label):
                raise ValueError(f"linha {line}: label invalido: {label}")
            if label in labels:
                raise ValueError(f"linha {line}: label duplicado: {label}")
            labels[label] = pc
            code = after.strip()
            if not code:
                break
        if not code:
            continue
        parts = code.replace(",", " ").split()
        mnemonic = parts[0].upper()
        if mnemonic not in OPS:
            raise ValueError(f"linha {line}: instrucao desconhecida: {mnemonic}")
        opcode, fmt = OPS[mnemonic]
        args = parts[1:]
        if len(args) != len(fmt):
            raise ValueError(f"linha {line}: {mnemonic} precisa de {len(fmt)} operandos")
        instructions.append((line, opcode, fmt, args))
        pc += 1 + sum(SIZES[c] for c in fmt)
        if pc > 65536:
            raise ValueError(f"linha {line}: programa excede 64 KiB")
    if pc == 0:
        raise ValueError("programa vazio")
    result = bytearray()
    for line, opcode, fmt, args in instructions:
        result.append(opcode)
        for kind, token in zip(fmt, args):
            if kind == "r":
                result.append(parse_register(token, line))
            else:
                value = immediate(token, labels, line)
                if kind == "i":
                    if not -(2**31) <= value <= 2**32 - 1:
                        raise ValueError(f"linha {line}: imediato excede 32 bits")
                    result += struct.pack("<I", value & 0xFFFFFFFF)
                elif kind == "a":
                    if not 0 <= value <= 0xFFFFFFFF:
                        raise ValueError(f"linha {line}: endereco de salto invalido")
                    result += struct.pack("<I", value)
                elif kind == "m":
                    if not 0 <= value <= 65532 or value % 4:
                        raise ValueError(f"linha {line}: endereco de memoria fora dos limites/desalinhado")
                    result += struct.pack("<H", value)
    assert len(result) == pc
    return struct.pack("<4sBBHI", b"WVM1", 1, 0, 0, len(result)) + result


def main():
    cli = argparse.ArgumentParser(description="Assembler WOLF-VM (arquivos .wva -> .wvm)")
    cli.add_argument("source", type=Path)
    cli.add_argument("-o", "--output", required=True, type=Path)
    args = cli.parse_args()
    try:
        code = assemble(args.source.read_text(encoding="utf-8"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(code)
        print(f"[WOLF-ASM] {args.output} ({len(code)} bytes, incluindo header)")
    except (ValueError, OSError) as exc:
        cli.error(str(exc))


if __name__ == "__main__":
    main()
