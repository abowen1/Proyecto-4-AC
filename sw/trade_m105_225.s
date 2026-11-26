# M105-225: bandas absolutas, presupuesto 100%, sin retiro por patrimonio.
# ISA base Espino, sin extensiones. Implementacion funcional sin optimizaciones.
# x2 SPI; x3 caja; x4 acciones; x5 precio; x6 estado;
# x7 presupuesto restante; x9 orden previa; x10..x14 temporales.
# Estados: 0 flat, 1 buying, 2 holding, 3 selling (salida enclavada).
.text
.global start
start:
    lui x2, 0x80010
    lui x3, 2
    addi x3, x3, 1808
    addi x4, x0, 0
    addi x6, x0, 0
    addi x7, x0, 0
    addi x9, x0, 0
    sw x0, 8(x2)
wait_price:
    lw x10, 0(x2)
    andi x10, x10, 1
    beq x10, x0, wait_price
    lw x5, 4(x2)

# Ejecutar localmente la orden anterior al precio que acaba de llegar.
    andi x10, x9, 63
    beq x10, x0, accounted
    addi x11, x0, 128
    bge x9, x11, fill_sell
fill_buy:
    addi x11, x3, -5
    addi x12, x0, 0
fill_buy_loop:
    beq x12, x10, fill_buy_done
    blt x11, x5, fill_buy_done
    sub x11, x11, x5
    addi x12, x12, 1
    jal x0, fill_buy_loop
fill_buy_done:
    beq x12, x0, accounted
    sub x13, x3, x11
    sub x7, x7, x13
    addi x3, x11, 0
    add x4, x4, x12
    jal x0, accounted
fill_sell:
    bge x4, x10, sell_quantity
    addi x10, x4, 0
sell_quantity:
    beq x10, x0, accounted
    addi x11, x3, 0
    addi x12, x10, 0
fill_sell_loop:
    add x11, x11, x5
    addi x12, x12, -1
    bne x12, x0, fill_sell_loop
    addi x11, x11, -5
    blt x11, x0, accounted
    addi x3, x11, 0
    sub x4, x4, x10
    bne x4, x0, accounted
    addi x6, x0, 0
    addi x7, x0, 0
accounted:
    addi x9, x0, 0

# La banda alta tiene prioridad mientras hay inventario.
    beq x4, x0, try_entry
    addi x10, x0, 225
    blt x5, x10, try_entry
    addi x6, x0, 3
try_entry:
    bne x6, x0, choose_action
    addi x10, x0, 105
    blt x10, x5, publish
# Estando flat, patrimonio = caja; fijar presupuesto de campana.
    addi x7, x3, 0
    addi x6, x0, 1
choose_action:
    addi x10, x0, 3
    beq x6, x10, propose_sell
    addi x10, x0, 1
    bne x6, x10, publish
    addi x10, x0, 105
    blt x10, x5, close_accumulation
    addi x11, x3, -5
    addi x12, x7, -5
    bge x12, x11, size_buy
    addi x11, x12, 0
size_buy:
    addi x10, x0, 0
    addi x12, x0, 63
size_buy_loop:
    beq x10, x12, size_buy_done
    blt x11, x5, size_buy_done
    sub x11, x11, x5
    addi x10, x10, 1
    jal x0, size_buy_loop
size_buy_done:
    beq x10, x0, close_accumulation
    ori x9, x10, 64
    jal x0, publish
close_accumulation:
    addi x6, x0, 0
    beq x4, x0, publish
    addi x6, x0, 2
    jal x0, publish
propose_sell:
    beq x4, x0, publish
    addi x10, x0, 63
    bge x4, x10, size_sell_done
    addi x10, x4, 0
size_sell_done:
    ori x9, x10, 128
publish:
    sw x9, 8(x2)
    jal x0, wait_price
