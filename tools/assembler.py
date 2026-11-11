#!/usr/bin/env python3
"""Assembler de dos pasadas para el subconjunto RV32E de este proyecto."""
import argparse
from pathlib import Path
import re
import sys


class AssemblyError(ValueError):
    pass


NAME = r'[A-Za-z_][A-Za-z_0-9]*'
R_OPS = {'add': (0, 0), 'sub': (0, 32), 'slt': (2, 0),
         'sltu': (3, 0), 'xor': (4, 0), 'or': (6, 0), 'and': (7, 0)}
I_OPS = {'addi': 0, 'slti': 2, 'sltiu': 3, 'xori': 4, 'ori': 6, 'andi': 7}
BRANCHES = {'beq': 0, 'bne': 1, 'blt': 4, 'bge': 5, 'bltu': 6, 'bgeu': 7}
SHIFTS = {'sll', 'srl', 'sra', 'slli', 'srli', 'srai'}


def register(token):
    if not re.fullmatch(r'x(?:[0-9]|1[0-5])', token):
        raise AssemblyError(f'registro inválido {token!r}; usar x0 a x15')
    return int(token[1:])


def number(token):
    try:
        return int(token, 0) if re.match(r'[+-]?0[xXbBoO]', token) else int(token, 10)
    except ValueError:
        raise AssemblyError(f'entero inválido {token!r}') from None


def signed(value, bits):
    if not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise AssemblyError(f'inmediato {value} fuera del rango con signo de {bits} bits')
    return value & ((1 << bits) - 1)


def operands(args, count):
    if len(args) != count or any(not a for a in args):
        raise AssemblyError(f'se esperaban {count} operandos separados por comas')


def memory(token):
    match = re.fullmatch(r'([^()\s]+)\s*\(\s*(x\d+)\s*\)', token)
    if not match:
        raise AssemblyError('usar desplazamiento(registro), por ejemplo 4(x2)')
    return signed(number(match[1]), 12), register(match[2])


def relative(token, pc, labels, bits):
    if re.fullmatch(NAME, token):
        if token not in labels:
            raise AssemblyError(f'etiqueta no definida: {token}')
        offset = labels[token] - pc
    else:
        offset = number(token)
    # Este procesador solo ejecuta instrucciones de 32 bits.
    if offset % 4:
        raise AssemblyError('el destino debe estar alineado a 4 bytes')
    return signed(offset, bits)


def encode(op, args, pc, labels):
    if op in SHIFTS:
        raise AssemblyError('desplazamientos desactivados en la ALU de Espino Core')
    if op in R_OPS:
        operands(args, 3)
        rd, rs1, rs2 = map(register, args)
        f3, f7 = R_OPS[op]
        return f7 << 25 | rs2 << 20 | rs1 << 15 | f3 << 12 | rd << 7 | 0x33
    if op in I_OPS:
        operands(args, 3)
        rd, rs1 = map(register, args[:2])
        imm = signed(number(args[2]), 12)
        return imm << 20 | rs1 << 15 | I_OPS[op] << 12 | rd << 7 | 0x13
    if op in ('lui', 'auipc'):
        operands(args, 2)
        rd, imm = register(args[0]), number(args[1])
        if not 0 <= imm <= 0xfffff:
            raise AssemblyError('LUI/AUIPC requieren un campo sin signo de 20 bits')
        return imm << 12 | rd << 7 | (0x37 if op == 'lui' else 0x17)
    if op in ('lw', 'sw', 'jalr'):
        operands(args, 2)
        reg = register(args[0])
        imm, base = memory(args[1])
        if op == 'sw':
            return (imm >> 5) << 25 | reg << 20 | base << 15 | 2 << 12 | (imm & 31) << 7 | 0x23
        return imm << 20 | base << 15 | (2 << 12 if op == 'lw' else 0) | reg << 7 | (0x03 if op == 'lw' else 0x67)
    if op in BRANCHES:
        operands(args, 3)
        rs1, rs2 = map(register, args[:2])
        imm = relative(args[2], pc, labels, 13)
        return ((imm >> 12) & 1) << 31 | ((imm >> 5) & 63) << 25 | rs2 << 20 | rs1 << 15 | BRANCHES[op] << 12 | ((imm >> 1) & 15) << 8 | ((imm >> 11) & 1) << 7 | 0x63
    if op == 'jal':
        operands(args, 2)
        rd = register(args[0])
        imm = relative(args[1], pc, labels, 21)
        return ((imm >> 20) & 1) << 31 | ((imm >> 1) & 1023) << 21 | ((imm >> 11) & 1) << 20 | ((imm >> 12) & 255) << 12 | rd << 7 | 0x6f
    raise AssemblyError(f'instrucción no admitida: {op}')


def assemble(source, max_words=512):
    """Primera pasada: direcciones. Segunda pasada: codificación y etiquetas."""
    labels, instructions, globals_ = {}, [], []
    for line_no, raw in enumerate(source.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        while match := re.match(rf'^({NAME}):', line):
            label = match[1]
            if label in labels:
                raise AssemblyError(f'línea {line_no}: etiqueta duplicada: {label}')
            labels[label] = 4 * len(instructions)
            line = line[match.end():].strip()
        if not line:
            continue
        if line in ('.text', '.section .text'):
            continue
        if line.startswith('.global '):
            name = line[len('.global '):].strip()
            if not re.fullmatch(NAME, name):
                raise AssemblyError(f'línea {line_no}: símbolo global inválido')
            globals_.append((name, line_no))
            continue
        if line.startswith('.'):
            raise AssemblyError(f'línea {line_no}: directiva no admitida: {line}')
        parts = line.split(None, 1)
        args = [a.strip() for a in parts[1].split(',')] if len(parts) == 2 else []
        instructions.append((line_no, parts[0], args))
    for name, line_no in globals_:
        if name not in labels:
            raise AssemblyError(f'línea {line_no}: símbolo global no definido: {name}')
    if not instructions:
        raise AssemblyError('programa vacío')
    if len(instructions) > max_words:
        raise AssemblyError(f'el programa excede las {max_words} palabras de RAM')
    words = []
    for index, (line_no, op, args) in enumerate(instructions):
        try:
            words.append(encode(op, args, 4 * index, labels))
        except AssemblyError as error:
            raise AssemblyError(f'línea {line_no}: {error}') from None
    return words


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('-o', '--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.source.resolve() == args.output.resolve():
            raise AssemblyError('entrada y salida deben ser archivos distintos')
        words = assemble(args.source.read_text(encoding='utf-8'))
        # No escribir hasta validar el programa completo.
        args.output.write_text(''.join(f'{word:08x}\n' for word in words), encoding='ascii')
    except (AssemblyError, OSError, UnicodeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    print(f'{args.source} -> {args.output}: {len(words)} palabras ({len(words)*4} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
