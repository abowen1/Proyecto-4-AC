# D original: SMA32, banda 1, sin techo de patrimonio ni protecciones.
# Orden previa ejecutada al precio actual, comision 5.
# x1=anillo RAM 0x600..0x67c, x2=SPI, x3=caja, x4=acciones,
# x5=precio, x6=suma32, x7=offset anillo, x8=muestras, x9=orden previa.
# x10..x13 temporales. Sin multiplicacion, division ni shifts.
.text
.global start
start:
    addi x1, x0, 1536
    lui x2, 0x80010
    lui x3, 2
    addi x3, x3, 1808
    addi x4, x0, 0
    addi x6, x0, 0
    addi x7, x0, 0
    addi x8, x0, 0
    addi x9, x0, 0
    sw x0, 8(x2)
wait_price:
    lw x10, 0(x2)
    andi x10, x10, 1
    beq x10, x0, wait_price
    lw x5, 4(x2)

# Contabilizar la orden que el maestro acaba de ejecutar.
    andi x10, x9, 63
    beq x10, x0, accounted
    addi x11, x0, 128
    bge x9, x11, fill_sell
fill_buy:
    addi x11, x3, -5
    blt x11, x0, accounted
    addi x12, x0, 0
fill_buy_loop:
    beq x12, x10, fill_buy_done
    blt x11, x5, fill_buy_done
    sub x11, x11, x5
    addi x12, x12, 1
    jal x0, fill_buy_loop
fill_buy_done:
    beq x12, x0, accounted
    addi x3, x11, 0
    add x4, x4, x12
    jal x0, accounted
fill_sell:
    bge x4, x10, fill_sell_quantity
    addi x10, x4, 0
fill_sell_quantity:
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
accounted:
    addi x9, x0, 0

# No leer entradas del anillo antes de escribirlas por primera vez.
    add x11, x1, x7
    addi x12, x0, 32
    beq x8, x12, remove_old
    addi x8, x8, 1
    jal x0, append_price
remove_old:
    lw x10, 0(x11)
    sub x6, x6, x10
append_price:
    sw x5, 0(x11)
    add x6, x6, x5
    addi x7, x7, 4
    andi x7, x7, 127
    bne x8, x12, publish

# suma32 - 32*precio >32 compra, <-32 vende; igualdad mantiene.
# Incluye el precio actual y evita redondear la media.
    add x10, x5, x5
    add x10, x10, x10
    add x10, x10, x10
    add x10, x10, x10
    add x10, x10, x10
    sub x10, x6, x10
    blt x12, x10, propose_buy
    addi x12, x0, -32
    blt x10, x12, propose_sell
    jal x0, publish
propose_buy:
    addi x11, x3, -5
    blt x11, x0, publish
    addi x12, x0, 63
    addi x13, x0, 0
size_buy_loop:
    beq x13, x12, size_buy_done
    blt x11, x5, size_buy_done
    sub x11, x11, x5
    addi x13, x13, 1
    jal x0, size_buy_loop
size_buy_done:
    beq x13, x0, publish
    ori x9, x13, 64
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
