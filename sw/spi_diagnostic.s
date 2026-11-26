# Solo diagnóstico: devolver los seis bits bajos del precio recibido.
# Acción 00=mantener. Comprueba MISO variable y respuesta en transacción n+1.
.text
.global start
start:
    lui x1, 0x80010
    sw x0, 8(x1)
wait_price:
    lw x2, 0(x1)
    andi x2, x2, 1
    beq x2, x0, wait_price
    lw x3, 4(x1)
    andi x3, x3, 63
    sw x3, 8(x1)
    jal x0, wait_price
