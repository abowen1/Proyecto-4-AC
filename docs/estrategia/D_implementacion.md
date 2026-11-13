# D elegida e implementada en Espino

**Etapa posterior:** ya se implementaron y compararon [A/shifter acotado y B/QCAP](../informe/03_hardware_2026-11-12/README.md), manteniendo D. A se recomienda con 64,210 ciclos promedio y 257 de máximo observado. Ambos autodiagnósticos físicos pasaron al programar y al reconectar. El reset común del SoC se amplió a 63 ciclos tras detectar un fallo real de arranque; todas las variantes se volvieron a medir con ese reset. SPI físico con la maestra aún está pendiente.

**Versión actual:** la [vía rápida de 63](../informe/02_via_rapida_63_2026-11-12/README.md) se implementó, validó y conservó. `sw/trade.s` tiene 102 instrucciones y utiliza x14; `sw/trade_base_84.s/.hex` conserva la base inicial descrita abajo, de 84 instrucciones. La estrategia y las reglas contables son idénticas. En la práctica completa el promedio baja de 121,315 a 89,378 ciclos y el máximo observado de 1.484 a 802. La imagen se regeneró sin programar la placa. Los apartados siguientes conservan la evidencia inicial, anterior a esa mejora.

Acuerdo del equipo confirmado el 12 de noviembre de 2026: **reversión a la media de 32 muestras, banda 1, sin retiro por patrimonio**. No incluye pánico, filtro de tendencia ni límite de exposición. Las pruebas previas de retiro en 20.000 o 30.000 quedan descartadas para esta versión.

## Reglas reproducibles

- Caja inicial 10.000, cero acciones, comisión 5 por orden efectivamente ejecutada.
- La ventana incluye el precio actual y los 31 anteriores. Mantener hasta tener 32 muestras; primera señal posible en tick 31.
- Comprar si `suma32 - 32*precio > 32`; vender si es menor que `-32`; mantener en el resto, incluidas ambas igualdades. Sin división ni redondeo de la media.
- Compra: `q=min(63,max(0,(caja-5)//precio))`. Venta: `q=min(63,acciones)`. Mantener si q=0. El límite de 63 corresponde a cada orden, no a la posición total.
- La decisión se publica después de recibir el precio y se ejecuta al precio siguiente. Antes de calcular la nueva orden se actualiza la contabilidad local de la orden anterior, recortando la compra por caja disponible y la venta por inventario. Las ventas deben cubrir la comisión con caja más recaudación.
- No se liquida automáticamente al final; la última orden calculada no se ejecuta sin otro precio. El patrimonio final incluye acciones valoradas al último precio.
- No se consulta el número de tick para decidir ni se almacenan precios futuros. No hay condición de salida al alcanzar 20.000, 30.000 u otro patrimonio.

Referencia: `tools/backtest.py`, `run(prices,'reversion_media',Rules(),{'ventana':32,'banda':1})`, sin política adicional. Ejecutable: `sw/trade.s` y `sw/trade.hex`.

## Implementación inicial: base de 84, sin cambios al procesador

84 instrucciones estáticas, 336 bytes de programa. Anillo de 32 palabras, 128 bytes, en RAM `0x600..0x67c`; no se solapa con el código. Las entradas se escriben antes de leerse; no depende de valores iniciales en RAM sin inicializar. Estado contable y acumuladores permanecen en registros x1..x13. Todos los registros usados se inicializan o se asignan antes de consultarlos.

La suma de ventana se actualiza restando la muestra saliente y agregando la entrante. `32*precio` se calcula mediante cinco duplicaciones. Las cantidades y recaudaciones se calculan con bucles acotados a 63 iteraciones. No se requiere multiplicación, división, shifts, instrucciones nuevas ni periféricos nuevos.

`sw/hold.s` conserva la base anterior de mantener para las pruebas aisladas del protocolo. Cambiar `trade.s` a D no convierte esas pruebas en pruebas bursátiles: la equivalencia de D se verifica con un banco separado. No se modificaron los 13 archivos RTL, los pines, el reloj de 25 MHz ni el testbench original de Canvas.

## Evidencia obtenida

`tb/tb_strategy_d.sv` comprueba en cada precio: byte MISO igual a la orden previa, orden siguiente exacta, caja e inventario exactos, una lectura y una respuesta por precio, ausencia de instrucciones ilegales y valores desconocidos, y respuesta dentro del presupuesto. La caja y el inventario se observan en las escrituras reales de registros del procesador; no se sustituyen por la referencia.

| Prueba RTL con SPI | Precios | Máximo de ciclos de servicio | Promedio | Máximo de instrucciones | CPI de servicio agregado |
|---|---:|---:|---:|---:|---:|
| Práctica completa, sin espera ociosa | 20.000 | 1.484 | 121,315 | 675 | 2,203 |
| Primeros 2.000, período fijo 100 us | 2.000 | 1.227 | 112,338 | 547 | 2,215 |
| Extremos artificiales, sin espera ociosa | 816 | 1.484 | 843,648 | 675 | 2,222 |

Se mide desde `byte_done` hasta la escritura de DECISION, excluyendo el sondeo ocioso anterior al precio. El CPI de servicio es la suma de esos ciclos dividida por las instrucciones retiradas en esas ventanas; incluye la detección del precio y la publicación, no representa un kernel aritmético aislado.

**Diferencia entre pruebas:** en los 20.000 y en los extremos se conserva CPU a 25 MHz y SPI a 1 MHz, pero el emisor comienza el siguiente intercambio después de la respuesta, omitiendo la espera ociosa. Prueban equivalencia funcional y latencia de servicio; no son una ronda completa de período fijo. La prueba de los primeros 2.000 sí conserva el período oficial rápido de 100 us. El presupuesto conservador de servicio es 2.262 ciclos, 90,48 us; el máximo observado de 1.484 ciclos equivale a 59,36 us. Es un máximo observado, no una demostración de peor caso para todas las series posibles.

En los 20.000 precios: patrimonio **17.909**, caja 11.735, 63 acciones, 1.415 órdenes, comisiones 7.075 y drawdown máximo 7.017. Coincide con D Python anterior. Los primeros 2.000 terminan en 9.923; no confundir con el archivo completo. La serie extrema es exclusivamente técnica y alcanza patrimonio superior a 30.000 sin detener las operaciones; no es evidencia de rentabilidad financiera.

Las 29 pruebas unitarias y las seis pruebas previas de protocolo también pasaron. El ensamblado produce 84 palabras, frente a las ocho palabras del mantener anterior.

Evidencia por precio y resúmenes: [`../evidencias/D_2026-11-12/`](../evidencias/D_2026-11-12/).

## Imagen para placa

`make build` produjo `build/ac4.bin`, 32.220 bytes, SHA256 `f2df347d35b9ef1b74b82960aeba4b4378d6b2b242b6db8c75b10573ad0d4815`. Ocupación: 1.082/1.280 celdas lógicas, 12/16 BRAM. nextpnr estima Fmax 44,81 MHz y aprueba la restricción de 25 MHz. La frecuencia implementada sigue siendo 25 MHz.

Esta imagen contiene D y está generada, pero **no se cargó en la placa** durante esta implementación. La última prueba física confirmada sigue siendo botones/LED. El intercambio SPI físico con la maestra del curso y el comportamiento de inicio/reinicio de rondas siguen pendientes.

## Reproducir

Desde la raíz del repositorio:

```sh
make test
make test-d
python3 tools/verify_strategy_d.py --ticks 2000 --name practica_2000_ronda3
python3 tools/verify_strategy_d.py --edges --fast --name extremos
make build
```

Para comprobar también los 20.000 con período fijo, ejecutar `python3 tools/verify_strategy_d.py --name practica_20000_periodo_fijo`; es más lento y no forma parte de la evidencia anterior. Las pruebas no programan la placa. No se requieren paquetes Python adicionales.

## Trabajo necesario siguiente

**Perfil y atajo completados el 12 de noviembre:** [perfil inicial y Amdahl](../informe/01_perfil_D_2026-11-12/README.md) y [evaluación del atajo con nuevo perfil](../informe/02_via_rapida_63_2026-11-12/README.md). Se conserva abajo el orden previsto; el punto 1 y la mejora de software ya están resueltos. Las alternativas de hardware se deben diseñar usando el perfil nuevo.

1. Perfil realizado: recepción/contabilidad, actualización de ventana, señal y tamaño de orden. Los tres bucles de órdenes ocupan 43,69% del servicio promedio; los dos de compra dominan 93,80% del tick más lento.
2. Usar ese perfil para estimar Amdahl y seleccionar, implementar y comparar **al menos dos alternativas de hardware**, como exige §3.3 del enunciado, contra esta base solo software. Cumplir el plazo con esta base no elimina ese requisito.
3. Mantener las decisiones de D idénticas al comparar variantes, para distinguir aceleración de un cambio bursátil. Medir ciclos, CPI, recursos, Fmax, Ops/s y roofline; justificar la variante final.
4. Probar la imagen seleccionada con SPI físico y preparar la entrega evaluada desde `pre-entrega` hacia `main`.
