# Dependencias consecutivas, rd=rs1, x0, precio cero y presupuesto de 32 bits.
.text
.global start
start:
    addi x1, x0, 1000
    addi x2, x0, 100
    qcap x3, x1, x2
    qcap x4, x3, x2
    qcap x5, x1, x3
    qcap x6, x1, x0
    lui x7, 0xfffff
    qcap x8, x7, x2
    addi x9, x0, 63
    qcap x10, x9, x3
    addi x11, x0, 1
    qcap x12, x11, x11
    addi x13, x0, 100
    qcap x13, x13, x2
    qcap x0, x1, x2
    addi x14, x0, 7
    addi x1, x0, 10
    bne x3, x1, fail
    addi x1, x0, 0
    bne x4, x1, fail
    addi x1, x0, 63
    bne x5, x1, fail
    addi x1, x0, 0
    bne x6, x1, fail
    addi x1, x0, 63
    bne x8, x1, fail
    addi x1, x0, 6
    bne x10, x1, fail
    addi x1, x0, 1
    bne x12, x1, fail
    addi x1, x0, 1
    bne x13, x1, fail
    addi x1, x0, 7
    bne x14, x1, fail
    lui x2, 0x80000
    addi x1, x0, 15
    sw x1, 4(x2)
    addi x1, x0, 181
    sw x1, 0(x2)
    lui x15, 0x80010
    sw x14, 8(x15)
done:
    jal x0, done
fail:
    lui x2, 0x80000
    addi x1, x0, 1
    sw x1, 4(x2)
    addi x1, x0, 238
    sw x1, 0(x2)
    lui x15, 0x80010
    addi x14, x0, 254
    sw x14, 8(x15)
    jal x0, fail
