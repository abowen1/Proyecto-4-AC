# Base de integración AC4, sin estrategia bursátil.
# x1=base SPI, x2=estado, x3=último precio recibido.
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
    sw x0, 8(x1)
    jal x0, wait_price
