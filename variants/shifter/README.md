# Alternativa A: desplazamientos inmediatos acotados

Implementa resultados RV32 exactos para `SLLI` de 1, 5 y 6 bits y `SRLI` de 1 bit, siempre sobre operandos de 32 bits. No es un barrel shifter general ni una truncacion a 8/16 bits. El decoder marca como ilegales las otras cantidades, shifts por registro y shifts aritméticos. El ensamblador los rechaza con `--isa shifter`.

Se reemplazan solo `espino_alu.v` y `espino_decoder.v`, conservando el resto de Pochoco y el reloj de 25 MHz. `tools/hardware_variants.py` selecciona los reemplazos sin duplicar módulos. `sw/trade_shifter.s` conserva D y usa búsqueda binaria acotada a seis bits para compras y multiplicación binaria para ventas. La media y la política bursátil son idénticas a la referencia.

```sh
make test-hardware
make build-shifter
python3 tools/verify_strategy_d.py --variant shifter --fast --profile --name hw_shifter_20000
```

Imagen local: `build/hardware/shifter/soc.bin`. La prueba física de cálculo utiliza otro programa con comprobaciones internas, `sw/shifter_diagnostic.s`, que muestra cuatro LED y A5 solo si pasan; un fallo muestra un LED y un código E1..EB. Se genera con `python3 tools/hardware_variants.py shifter --program sw/shifter_diagnostic.s --name shifter_diagnostic`. El programa bursátil espera precios SPI y no muestra A5.

Se aplica el reset común corregido de 63 ciclos en `rtl/pochoco_soc.v`, también a software y QCAP. El autodiagnóstico pasó en la placa después de programar y de desconectar/reconectar USB; la prueba de transacciones SPI físicas permanece pendiente.

La versión inicial con barrel shifter lógico general necesitaba 1.346/1.280 celdas y se descartó; sus fuentes y registros se conservan en `docs/informe/03_hardware_2026-11-12/descartes/barrel32/`.

Resultados, limitaciones y comparación: [material del informe](../../docs/informe/03_hardware_2026-11-12/README.md).
