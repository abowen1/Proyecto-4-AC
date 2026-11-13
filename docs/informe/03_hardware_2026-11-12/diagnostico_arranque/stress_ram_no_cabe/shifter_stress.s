.text
.global init
init:
    addi x2, x0, 1001
    sw x2, 1792(x0)
start:
    lui x1, 0x80000
    srli x3, x1, 1
    slli x4, x1, 1
    addi x1, x0, 255
    slli x5, x1, 5
    slli x6, x1, 6
    addi x7, x0, -1
    srli x8, x7, 1
    slli x9, x7, 5
    slli x10, x7, 6
    slli x11, x3, 1
    srli x12, x11, 1
    addi x13, x0, 1
    addi x14, x0, 7
    lui x1, 262144
    addi x1, x1, 0
    addi x15, x0, 225
    bne x3, x1, stress_fail
    addi x1, x0, 0
    addi x15, x0, 226
    bne x4, x1, stress_fail
    lui x1, 2
    addi x1, x1, -32
    addi x15, x0, 227
    bne x5, x1, stress_fail
    lui x1, 4
    addi x1, x1, -64
    addi x15, x0, 228
    bne x6, x1, stress_fail
    lui x1, 524288
    addi x1, x1, -1
    addi x15, x0, 229
    bne x8, x1, stress_fail
    lui x1, 0
    addi x1, x1, -32
    addi x15, x0, 230
    bne x9, x1, stress_fail
    lui x1, 0
    addi x1, x1, -64
    addi x15, x0, 231
    bne x10, x1, stress_fail
    lui x1, 524288
    addi x1, x1, 0
    addi x15, x0, 232
    bne x11, x1, stress_fail
    lui x1, 262144
    addi x1, x1, 0
    addi x15, x0, 233
    bne x12, x1, stress_fail
    addi x1, x0, 1
    addi x15, x0, 234
    bne x13, x1, stress_fail
    addi x1, x0, 7
    addi x15, x0, 235
    bne x14, x1, stress_fail
    jal x0, stress_next
stress_fail:
    lui x1, 16
    add x2, x2, x1
stress_next:
    lw x14, 1792(x0)
    andi x15, x2, 2047
    bne x14, x15, stress_mem_error
    jal x0, stress_ring
stress_mem_error:
    lui x1, 16
    add x2, x2, x1
stress_ring:
    andi x15, x2, 31
    slli x15, x15, 1
    slli x15, x15, 1
    addi x15, x15, 1536
    xori x14, x2, -1
    sw x14, 0(x15)
    lw x1, 0(x15)
    beq x1, x14, stress_decrement
    lui x1, 16
    add x2, x2, x1
stress_decrement:
    addi x2, x2, -1
    andi x14, x2, 2047
    sw x14, 1792(x0)
    bne x14, x0, start
    lui x1, 0x80000
    bne x2, x0, report_fail
    addi x14, x0, 15
    sw x14, 4(x1)
    addi x14, x0, 165
    sw x14, 0(x1)
    jal x0, stress_done
report_fail:
    ori x14, x2, 1
    sw x14, 4(x1)
    sw x2, 0(x1)
stress_done:
    jal x0, stress_done
