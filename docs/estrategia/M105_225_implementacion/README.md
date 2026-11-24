# M105-225: implementación funcional y validación de las etapas 1 a 3

24 de noviembre de 2026. **Implementación base completada y pruebas aprobadas.** Se conserva M105-225 como nombre oficial. El equipo ya seleccionó sus bandas 105/225 y presupuesto del 100%; este trabajo las traslada a Espino sin cambiar la estrategia ni las reglas del mercado.

**Punto de parada solicitado: después de implementar, comprobar equivalencia y pasar integración.** No se hizo perfil de rendimiento, optimización de software o hardware, síntesis, place-and-route, generación de bitstream ni programación de la placa. El plazo por precio se verificó como requisito de integración, no como estudio de optimización.

## Implementación

- [Assembly base](../../../sw/trade_m105_225.s): 85 instrucciones (340 bytes), dentro de las 512 palabras disponibles. Solo ISA original; sin shifts,QCAP,multiplicación ni división por hardware.
- [HEX del programa](../../../sw/trade_m105_225.hex), salida del ensamblador para simulación. **No es un bitstream de FPGA.**
- [Referencia Python](../../../tools/m105_225.py): conserva exactamente las clases de la política financiera elegida.
- [Banco de equivalencia](../../../tb/tb_m105_225.sv): instancia el SoC y comunica precios/respuestas por SPI bit a bit. Monitorea decisiones, caja, acciones, estado y presupuesto restante.

Estados de la estrategia: espera en caja, acumulación, mantenimiento y liquidación enclavada. Al recibir cada precio primero se contabiliza la orden previa al precio actual. Luego se emite la próxima decisión. Compra con precio observado<=105, vende desde>=225, máximo 63 acciones por orden y comisión 5 por llenado ejecutado. La venta continúa aunque el precio baje de 225. Al salir de la banda baja se cierra la acumulación y no se reinicia mientras la campaña siga abierta. Puede reentrar después de liquidar. No hay retiro por patrimonio, stop ni venta final forzada.

La implementación conserva en x3 la caja, x4 el inventario, x5 el precio, x6 el estado y x7 el presupuesto restante. No necesita el anillo SMA de D. La división y los productos por cantidad se resuelven con bucles simples acotados por 63; no se añadieron vías rápidas ni instrucciones nuevas.

## Evidencia de aprobación

| Verificación | Cobertura | Resultado |
|---|---|---|
| Regresión unitaria | 48 pruebas, incluidas 6 específicas nuevas |PASS |
| Protocolo existente | mantener y diagnóstico en 10 ms, 1 ms y 0,1 ms: 6 rondas |PASS |
| Casos técnicos de M | 5 casos/558 ticks en Icarus y los mismos 5 en Verilator |PASS |
| Equivalencia completa Python/SoC | 78 series×20.000 =1.560.000 ticks |PASS |
| Integración con períodos fijos | 48 precios con compras/ventas, en las 3 velocidades |PASS |
| Maestra oficial del curso | 4/4 chequeos y contabilidad por tick en cada velocidad técnica |PASS |
| Maestra oficial con Meta | 2.000 ticks, período 0,1 ms, Icarus,4/4 chequeos y referencia exacta |PASS |

Las 78 series son las mismas 70 recreadas y 8 oficiales usadas para elegir la variante; sus hashes se comprueban antes de simular. Los resultados de M105-225 ejecutada en el procesador coinciden con los seleccionados, incluida su media final **18.079,333333333332**. No se descargaron ni regeneraron precios.

La prueba completa utiliza Verilator para ejecutar el RTL del procesador, memoria y periféricos con el SPI real del diseño. Cada serie arranca en una instancia nueva del SoC, con caja 10.000 e inventario cero. Se acorta únicamente la espera ociosa entre transacciones para la equivalencia funcional; se conserva el reloj 25 MHz, SPI 1 MHz y la comprobación del presupuesto de respuesta correspondiente al período 0,1 ms. Las rondas separadas con períodos fijos conservan todas las esperas de 0,1 ms, 1 ms y 10 ms.

Icarus valida adicionalmente los casos técnicos, el testbench oficial con Meta y la regresión SPI existente, conservando su semántica de valores desconocidos. El banco comprueba una lectura/respuesta por precio, ausencia de precios perdidos, consumo de NEW_PRICE, respuesta MISO de la decisión anterior y ausencia de instrucciones ilegales. Las decisiones realmente emitidas se vuelven a ejecutar con la contabilidad Python para comprobar patrimonio, órdenes, comisiones y caída, además de los valores internos observados en el procesador.

Los casos técnicos incluyen umbrales 104/105/106 y 224/225/226, salto entre observación y ejecución, caja limitada, cantidades parciales, liquidación persistente, cierre de acumulación, reentrada y posición abierta al terminar. Incluyen precios artificiales 1..255 para estresar caminos de ejecución; su rentabilidad no se usa como evidencia financiera. Las pruebas unitarias incluyen prefijos causales y una orden pendiente al final que no debe ejecutarse.

La maestra oficial se conserva en `tb/tb_proyecto_4.sv`. Su adaptador cambia solo rutas, cantidad de ticks, período y el tipado de localparam necesario para Icarus. No se alteran contabilidad, comisiones, SPI ni chequeos. La prueba Meta de 2000 ticks no abre posiciones en ese prefijo; las rondas técnicas y las 78 series completas sí ejercitan compras/ventas.

## Reproducción

Desde la raíz de Desarrollo AC4, con Python 3.10+, Icarus Verilog, Yosys-config, Verilator y las herramientas C++ de compilación:

```sh
make assemble-m105-225
make test-m105-225-unit
make test-m105-225-equivalence
make test-m105-225-integration
# Todas las anteriores junto con la regresión general:
make test-m105-225
```

No generan bitstreams ni programan la placa. Verilator solo compila un ejecutable de simulación. Para evitar limitaciones de GNU Make con espacios en rutas, sus fuentes se copian sin cambios a un directorio temporal; no se altera el RTL. La equivalencia también admite `python3 -B tools/test_all_m105_225.py --engine iverilog`, más lento.

Los 78 CSV se buscan primero en las carpetas hermanas de material Canvas y series recreadas. Si esas carpetas no están disponibles, el verificador puede usar las entradas oficiales y el archivo de recreadas publicados en la documentación del repositorio. [series.json](series.json) fija los hashes y resultados financieros esperados.

## Archivos de evidencia

- [Validación consolidada y hashes de fuentes](validacion.json).
- [Equivalencia de las 78 series](equivalencia_78.json) y [tabla de resultados](resultados_78.csv).
- [Casos técnicos en ambos simuladores](casos_tecnicos.json).
- [Integración con tres períodos](integracion_tres_periodos.json).
- [Canvas Meta 2000](canvas_meta_2000.json) y [salida original](canvas_meta_2000.txt).
- [Canvas 0,1 ms](canvas_100000.txt), [Canvas 1 ms](canvas_1000000.txt), [Canvas 10 ms](canvas_10000000.txt).
- [Regresión general y SPI](regresion.txt).

Las trazas completas, referencias y registros individuales se conservan en `build/m105_225/` y `build/canvas_m105_225/`; son regenerables. Se archiva un hash del programa exacto compartido por todos los ensayos.

## Estado al detener el trabajo

M105-225 ya está implementada y comprobada como base software. **El RTL previo, los programas D y sus objetivos históricos se conservaron.** `build-final` y `program-final` todavía corresponden a D con shifter; no representan la futura imagen de M. La placa no se tocó y esta simulación no certifica una prueba física.

La siguiente etapa, fuera de este trabajo, es medir M, escoger optimizaciones justificadas, volver a comprobar equivalencia y después generar/probar su imagen de FPGA. Las mediciones de D no se trasladan automáticamente a M.
