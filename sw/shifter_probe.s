.text
.global start
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
    bne x3, x1, fail
    addi x1, x0, 0
    addi x15, x0, 226
    bne x4, x1, fail
    lui x1, 2
    addi x1, x1, -32
    addi x15, x0, 227
    bne x5, x1, debug_value
    lui x1, 4
    addi x1, x1, -64
    addi x15, x0, 228
    bne x6, x1, fail
    lui x1, 524288
    addi x1, x1, -1
    addi x15, x0, 229
    bne x8, x1, fail
    lui x1, 0
    addi x1, x1, -32
    addi x15, x0, 230
    bne x9, x1, fail
    lui x1, 0
    addi x1, x1, -64
    addi x15, x0, 231
    bne x10, x1, fail
    lui x1, 524288
    addi x1, x1, 0
    addi x15, x0, 232
    bne x11, x1, fail
    lui x1, 262144
    addi x1, x1, 0
    addi x15, x0, 233
    bne x12, x1, fail
    addi x1, x0, 1
    addi x15, x0, 234
    bne x13, x1, fail
    addi x1, x0, 7
    addi x15, x0, 235
    bne x14, x1, fail
    lui x2, 0x80000
    addi x1, x0, 15
    sw x1, 4(x2)
    addi x1, x0, 165
    sw x1, 0(x2)
    lui x15, 0x80010
    sw x14, 8(x15)
done:
    jal x0, done
fail:
    lui x2, 0x80000
    addi x1, x0, 1
    sw x1, 4(x2)
    sw x15, 0(x2)
    lui x15, 0x80010
    addi x14, x0, 254
    sw x14, 8(x15)
fail_done:
    jal x0, fail_done
debug_value:
    addi x10, x5, 0
    addi x11, x1, 0
    lui x2, 0x80000
probe_loop:
    lw x12, 8(x2)
    andi x13, x12, 2
    beq x13, x0, probe_actual
    addi x3, x11, 0
    jal x0, probe_select
probe_actual:
    addi x3, x10, 0
probe_select:
    andi x13, x12, 1
    beq x13, x0, probe_emit
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
    srli x3, x3, 1
probe_emit:
    sw x3, 0(x2)
    addi x13, x12, 1
    sw x13, 4(x2)
    jal x0, probe_loop
