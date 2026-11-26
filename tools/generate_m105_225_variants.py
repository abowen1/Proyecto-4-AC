"""Tres implementaciones equivalentes: despacho rapido y aritmetica acotada6 bits."""
from pathlib import Path
from backtest import ROOT

def quantity(variant,dest,prefix):
    if variant=='qcap':return f'    qcap {dest}, x11, x5\n'
    if variant=='shifter':fast='    slli x13, x5, 6\n'
    else:fast='    add x13, x5, x5\n'+'    add x13, x13, x13\n'*5
    text=fast+'    sub x13, x13, x5\n'+f'    blt x11, x13, {prefix}_partial\n    addi {dest}, x0, 63\n    jal x0, {prefix}_done\n{prefix}_partial:\n    addi {dest}, x0, 0\n'
    for bit in (32,16,8,4,2,1):
        if variant=='shifter':text+=('    slli x13, x5, 5\n' if bit==32 else '    srli x13, x13, 1\n')
        elif bit==1:text+='    addi x13, x5, 0\n'
        else:text+='    add x13, x5, x5\n'+'    add x13, x13, x13\n'*(bit.bit_length()-2)
        text+=f'    blt x11, x13, {prefix}_skip_{bit}\n    sub x11, x11, x13\n    addi {dest}, {dest}, {bit}\n{prefix}_skip_{bit}:\n'
    return text+f'{prefix}_done:\n'

def product(prefix):
    text='    addi x15, x0, 0\n    addi x10, x5, 0\n'
    for bit in (1,2,4,8,16,32):
        text+=f'    andi x13, x12, {bit}\n    beq x13, x0, {prefix}_skip_{bit}\n    add x15, x15, x10\n{prefix}_skip_{bit}:\n'
        if bit!=32:text+='    add x10, x10, x10\n'
    return text

def main():
    base=(ROOT/'sw/trade_m105_225.s').read_text()
    for variant in ('software','shifter','qcap'):
        text=base.replace('# ISA base Espino, sin extensiones. Implementacion funcional sin optimizaciones.',f'# Variante optimizada {variant}: misma politica y mismos registros observables.\n# x1=105,x8=225,x14=2(holding); cantidades/productos acotados a seis bits.')
        text=text.replace('    sw x0, 8(x2)\nwait_price:','    sw x0, 8(x2)\n    addi x1, x0, 105\n    addi x8, x0, 225\n    addi x14, x0, 2\nwait_price:')
        a=text.index('fill_buy:\n');b=text.index('fill_sell:\n',a)
        text=text[:a]+'''fill_buy:
    addi x11, x3, -5
    blt x11, x5, accounted
'''+quantity(variant,'x12','fill_quantity')+'''    bge x10, x12, fill_quantity_clipped
    addi x12, x10, 0
fill_quantity_clipped:
'''+product('buy_product')+'''fill_buy_done:
    addi x11, x3, -5
    sub x11, x11, x15
    sub x13, x3, x11
    sub x7, x7, x13
    addi x3, x11, 0
    add x4, x4, x12
    jal x0, accounted
'''+text[b:]
        a=text.index('    addi x11, x3, 0\n',text.index('fill_sell:\n'));b=text.index('    blt x11, x0, accounted',a)
        text=text[:a]+'''    addi x12, x10, 0
'''+product('sell_product')+'''fill_sell_done:
    add x11, x3, x15
    addi x11, x11, -5
'''+text[b:]
        text=text.replace('    sub x4, x4, x10\n','    sub x4, x4, x12\n')
        a=text.index('# La banda alta');b=text.index('choose_action:\n',a)
        text=text[:a]+'''# Despacho plano primero: evita trabajo sin inventario; constantes en registros.
    bne x6, x0, position_state
    blt x1, x5, publish
    addi x7, x3, 0
    addi x6, x0, 1
    jal x0, choose_action
position_state:
    beq x6, x14, holding_state
    beq x4, x0, choose_action
    blt x5, x8, choose_action
    addi x6, x0, 3
'''+text[b:]
        text=text.replace('    addi x10, x0, 105\n    blt x10, x5, close_accumulation','    blt x1, x5, close_accumulation')
        a=text.index('size_buy:\n');b=text.index('close_accumulation:\n',a)
        text=text[:a]+'''size_buy:
    blt x11, x5, close_accumulation
'''+quantity(variant,'x10','size_quantity')+'''size_buy_done:
    ori x9, x10, 64
    jal x0, publish
'''+text[b:]
        text=text.replace('    addi x10, x0, 63\n    bge x4, x10, size_sell_done','    addi x10, x14, 0\n    bge x4, x10, size_sell_done')
        text=text.replace('propose_sell:\n','holding_state:\n    blt x5, x8, publish\n    addi x6, x0, 3\npropose_sell:\n')
        text=text.replace('    addi x10, x14, 0\n','    addi x10, x0, 63\n')
        suffix='soft'  if variant=='software' else variant
        (ROOT/f'sw/trade_m105_225_{suffix}.s').write_text(text)

if __name__=='__main__':main()
