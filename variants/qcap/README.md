# Alternativa B: QCAP en custom-0

`qcap rd, rs1, rs2` calcula `min(63, unsigned(rs1)/unsigned(rs2[7:0]))`. Precio cero devuelve cero; el resto de bits de rs2 se ignora por contrato. Es una instrucción propia, no DIV estándar. Codificación R: opcode `0x0b`, funct3=0, funct7=0, registros RV32E x0..x15. Ensamblado explícito con `--isa qcap`.

La unidad reutiliza un restador de 14 bits y seis intentos binarios, desde `32*precio` hasta `precio`. Si algún bit 31..14 del presupuesto es uno, la cantidad saturada es necesariamente 63 para todo precio 1..255. Esto evita un divisor general de 32 bits. La unidad conserva la respuesta hasta el retiro de la instrucción; el core se detiene durante la operación y mantiene la decisión bursátil en assembly. Las seis iteraciones son ciclos de la unidad, no toda la latencia de la instrucción: también hay lectura de operandos, inicio y retiro.

Reemplaza decoder y etapa ID, y agrega `espino_qcap.v`. No modifica ALU, puertos SPI, memoria ni reloj. La señal `rf_ready` mantiene el stall hasta `done`, y el resultado se escribe una vez al retirar la instrucción. Se prueban dependencias consecutivas, rd=rs1, escritura descartada en x0, presupuestos completos de 32 bits, retención, reset y precios frontera.

`sw/trade_qcap.s` usa QCAP al dimensionar nuevas compras; la contabilidad previa conserva la implementación de software. Esa región ocupaba solo 7,38% del servicio después de la mejora de 63, por lo que Amdahl limita el beneficio total.

```sh
make test-hardware
make build-qcap
python3 tools/verify_strategy_d.py --variant qcap --fast --profile --name hw_qcap_20000
```

Imagen local: `build/hardware/qcap/soc.bin`. El diagnóstico físico separado `sw/qcap_diagnostic.s` comprueba sus resultados y muestra cuatro LED y B5 al pasar, o un LED y EE al fallar. Se genera con `python3 tools/hardware_variants.py qcap --program sw/qcap_diagnostic.s --name qcap_diagnostic`.

El reset de 63 ciclos de `rtl/pochoco_soc.v` es común a las tres implementaciones. El usuario confirmó B5/cuatro LED tras programar y después de desconectar/reconectar; no se afirma una prueba de transacciones SPI físicas.

Comparación y material para el informe: [resultados](../../docs/informe/03_hardware_2026-11-12/README.md).
