# M105-225: bandas absolutas, presupuesto 100%, sin retiro por patrimonio.
# Variante optimizada shifter: misma politica y mismos registros observables.
# x1=105,x8=225,x14=2(holding); cantidades/productos acotados a seis bits.
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
    addi x1, x0, 105
    addi x8, x0, 225
    addi x14, x0, 2
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
    blt x11, x5, accounted
    slli x13, x5, 6
    sub x13, x13, x5
    blt x11, x13, fill_quantity_partial
    addi x12, x0, 63
    jal x0, fill_quantity_done
fill_quantity_partial:
    addi x12, x0, 0
    slli x13, x5, 5
    blt x11, x13, fill_quantity_skip_32
    sub x11, x11, x13
    addi x12, x12, 32
fill_quantity_skip_32:
    srli x13, x13, 1
    blt x11, x13, fill_quantity_skip_16
    sub x11, x11, x13
    addi x12, x12, 16
fill_quantity_skip_16:
    srli x13, x13, 1
    blt x11, x13, fill_quantity_skip_8
    sub x11, x11, x13
    addi x12, x12, 8
fill_quantity_skip_8:
    srli x13, x13, 1
    blt x11, x13, fill_quantity_skip_4
    sub x11, x11, x13
    addi x12, x12, 4
fill_quantity_skip_4:
    srli x13, x13, 1
    blt x11, x13, fill_quantity_skip_2
    sub x11, x11, x13
    addi x12, x12, 2
fill_quantity_skip_2:
    srli x13, x13, 1
    blt x11, x13, fill_quantity_skip_1
    sub x11, x11, x13
    addi x12, x12, 1
fill_quantity_skip_1:
fill_quantity_done:
    bge x10, x12, fill_quantity_clipped
    addi x12, x10, 0
fill_quantity_clipped:
    addi x15, x0, 0
    addi x10, x5, 0
    andi x13, x12, 1
    beq x13, x0, buy_product_skip_1
    add x15, x15, x10
buy_product_skip_1:
    add x10, x10, x10
    andi x13, x12, 2
    beq x13, x0, buy_product_skip_2
    add x15, x15, x10
buy_product_skip_2:
    add x10, x10, x10
    andi x13, x12, 4
    beq x13, x0, buy_product_skip_4
    add x15, x15, x10
buy_product_skip_4:
    add x10, x10, x10
    andi x13, x12, 8
    beq x13, x0, buy_product_skip_8
    add x15, x15, x10
buy_product_skip_8:
    add x10, x10, x10
    andi x13, x12, 16
    beq x13, x0, buy_product_skip_16
    add x15, x15, x10
buy_product_skip_16:
    add x10, x10, x10
    andi x13, x12, 32
    beq x13, x0, buy_product_skip_32
    add x15, x15, x10
buy_product_skip_32:
fill_buy_done:
    addi x11, x3, -5
    sub x11, x11, x15
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
    addi x12, x10, 0
    addi x15, x0, 0
    addi x10, x5, 0
    andi x13, x12, 1
    beq x13, x0, sell_product_skip_1
    add x15, x15, x10
sell_product_skip_1:
    add x10, x10, x10
    andi x13, x12, 2
    beq x13, x0, sell_product_skip_2
    add x15, x15, x10
sell_product_skip_2:
    add x10, x10, x10
    andi x13, x12, 4
    beq x13, x0, sell_product_skip_4
    add x15, x15, x10
sell_product_skip_4:
    add x10, x10, x10
    andi x13, x12, 8
    beq x13, x0, sell_product_skip_8
    add x15, x15, x10
sell_product_skip_8:
    add x10, x10, x10
    andi x13, x12, 16
    beq x13, x0, sell_product_skip_16
    add x15, x15, x10
sell_product_skip_16:
    add x10, x10, x10
    andi x13, x12, 32
    beq x13, x0, sell_product_skip_32
    add x15, x15, x10
sell_product_skip_32:
fill_sell_done:
    add x11, x3, x15
    addi x11, x11, -5
    blt x11, x0, accounted
    addi x3, x11, 0
    sub x4, x4, x12
    bne x4, x0, accounted
    addi x6, x0, 0
    addi x7, x0, 0
accounted:
    addi x9, x0, 0

# Despacho plano primero: evita trabajo sin inventario; constantes en registros.
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
choose_action:
    addi x10, x0, 3
    beq x6, x10, propose_sell
    addi x10, x0, 1
    bne x6, x10, publish
    blt x1, x5, close_accumulation
    addi x11, x3, -5
    addi x12, x7, -5
    bge x12, x11, size_buy
    addi x11, x12, 0
size_buy:
    blt x11, x5, close_accumulation
    slli x13, x5, 6
    sub x13, x13, x5
    blt x11, x13, size_quantity_partial
    addi x10, x0, 63
    jal x0, size_quantity_done
size_quantity_partial:
    addi x10, x0, 0
    slli x13, x5, 5
    blt x11, x13, size_quantity_skip_32
    sub x11, x11, x13
    addi x10, x10, 32
size_quantity_skip_32:
    srli x13, x13, 1
    blt x11, x13, size_quantity_skip_16
    sub x11, x11, x13
    addi x10, x10, 16
size_quantity_skip_16:
    srli x13, x13, 1
    blt x11, x13, size_quantity_skip_8
    sub x11, x11, x13
    addi x10, x10, 8
size_quantity_skip_8:
    srli x13, x13, 1
    blt x11, x13, size_quantity_skip_4
    sub x11, x11, x13
    addi x10, x10, 4
size_quantity_skip_4:
    srli x13, x13, 1
    blt x11, x13, size_quantity_skip_2
    sub x11, x11, x13
    addi x10, x10, 2
size_quantity_skip_2:
    srli x13, x13, 1
    blt x11, x13, size_quantity_skip_1
    sub x11, x11, x13
    addi x10, x10, 1
size_quantity_skip_1:
size_quantity_done:
size_buy_done:
    ori x9, x10, 64
    jal x0, publish
close_accumulation:
    addi x6, x0, 0
    beq x4, x0, publish
    addi x6, x0, 2
    jal x0, publish
holding_state:
    blt x5, x8, publish
    addi x6, x0, 3
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
