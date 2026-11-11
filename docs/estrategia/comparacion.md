# Comparación exploratoria de cinco referencias

El enunciado propone familias de algoritmos, no cuatro estrategias completamente especificadas. Se implementó una variante sencilla de cada familia, con parámetros fijados antes de ejecutar la comparación. No hubo búsqueda de los parámetros que más ganan. Estas referencias no reemplazan la propuesta de la Coni ni constituyen una decisión final del equipo.

## Qué simula cada herramienta

- `tools/backtest.py`: algoritmo, byte de orden, ejecución al precio siguiente y contabilidad. Permite probar rápidamente todos los precios. Asume que cada decisión está lista a tiempo.
- `tools/verify_market.py`: extrae literalmente del testbench Canvas la tarea `ejecutar` y las variables contables; las ejecuta con Icarus usando las mismas decisiones y precios de Python. Compara caja, acciones, patrimonio, órdenes y drawdown en cada tick de las cinco estrategias completas, más casos límite. No sustituye el test de protocolo ni ejecuta assembly.
- `tb/tb_proyecto_4.sv`: simula la maestra SPI contra el SoC real y ejecuta la contabilidad oficial. Sirve también para evaluar estrategias, una vez implementadas en assembly. Por defecto usa solo 2.000 precios y la ronda rápida.

## Reglas comunes

Inicialización independiente de cada simulación: caja 10.000, cero acciones, decisión pendiente mantener. Comisión 5 por orden ejecutada. Los valores se leen de las constantes del testbench original.

En cada tick, primero se ejecuta la decisión anterior al precio que acaba de llegar; luego se observa ese precio y se prepara la decisión siguiente. No se puede mirar el próximo precio. La última decisión calculada queda sin ejecutar. Las acciones restantes se valoran al último precio, sin venta forzada al cerrar la serie.

La señal de cada algoritmo es comprar, vender o neutral. Todos comparten la misma regla de cantidades:

- Comprar: pedir `min(63, floor((caja - comisión)/precio_actual))`, limitado por abajo a cero. La maestra vuelve a limitar la compra con el precio de ejecución real del siguiente tick.
- Vender: pedir `min(63, acciones_actuales)`; la maestra valida inventario y comisión en el siguiente tick.
- Neutral o cantidad cero: mantener, byte 0x00.

Esto permite aumentar o reducir una posición durante varios ticks consecutivos si la señal persiste. No se define un tope de 63 para el inventario total: 63 es el máximo POR ORDEN. La contabilidad local conoce su orden anterior y el precio al que se ejecutó, sin consultar patrimonio a la maestra.

Todas las señales usan enteros; se comparan fracciones por productos cruzados. No se usan floats, precios futuros ni entrenamiento. Durante el llenado inicial de la ventana se mantiene. Los umbrales son estrictos: justo en la banda se mantiene.

## Variantes iniciales

| Familia | Parámetros | Compra | Venta |
|---|---|---|---|
| Mantener | Ninguno | Nunca | Nunca |
| Medias móviles | SMA corta 8, larga 32, banda 1 | SMA8 − SMA32 > 1 | SMA8 − SMA32 < −1 |
| Momentum | Retardo 8, banda 2 | Precio actual − precio de hace 8 ticks > 2 | Diferencia < −2 |
| Regresión lineal incremental | Ventana 16, predicción un tick, banda 1 | Precio predicho − actual > 1 | Diferencia < −1 |
| Reversión a la media | SMA32, banda 2 | SMA32 − precio actual > 2 | Diferencia < −2 |

La banda neutra mantiene la posición: no significa venderla automáticamente.

### Regresión

Se ajusta y=a*x+b a los últimos 16 precios, x=0..15, y se predice x=16. Se conservan suma de precios `Sy` y suma ponderada `Sxy`. Al retirar el precio más antiguo `old` y agregar `new`:

`Sxy_nueva = Sxy_anterior - (Sy_anterior - old) + 15*new`

`Sy_nueva = Sy_anterior - old + new`

Con `Sx=120`, `Sxx=1240`, `D=16*Sxx-Sx*Sx=5440` y `A=16*Sxy-Sx*Sy`, se compara `Sy*D + A*(256-Sx) - precio_actual*16*D` con `±16*D`. Así no hace falta redondear ni dividir para obtener la señal. La prueba automatizada contrasta el estado incremental con el cálculo completo de cada ventana.

## Resultados y reproducción

Ejecutar desde la raíz:

```sh
make test-market compare
```

Resultados ordenados en `comparacion/RESULTADOS.md`, configuración y hashes en `comparacion/configuracion.json`, verificación de contabilidad en `comparacion/validacion_contabilidad.json`. Cada CSV incluye orden aplicada, orden siguiente, señal, cantidad ejecutada, caja, acciones, patrimonio, comisiones y drawdown acumulado.

Se comparan la serie completa y sus primeros 2.000 precios, con estado y caja reiniciados en cada ejecución. Los 2.000 precios son un prefijo de la misma serie: NO son una validación independiente. Patrimonio final y máximo drawdown son magnitudes distintas; una estrategia puede terminar ganando y haber sufrido caídas importantes.

El benchmark adicional comprar y mantener reproduce la fórmula de Canvas: compra máxima al PRIMER precio y mantiene. Es una referencia idealizada separada de las cinco candidatas: no aplica el desfase SPI ni el límite de 63 a esa compra inicial. No usarlo como una sexta estrategia ejecutable sin adaptar esas condiciones.

## Límites

Los resultados incluyen comisiones, no son ganancias brutas. Comparan estas variantes concretas en esta única serie; otra ventana, banda, cantidad o serie puede cambiar el ranking. No se optimizaron parámetros usando los resultados. No prueban que se pueda cumplir el deadline de ninguna de las tres rondas: Python no simula instrucciones, ciclos, frecuencia, recursos FPGA ni fallos de comunicación. En esta comparación ideal las tres velocidades producirían el mismo patrimonio si todas las respuestas llegan a tiempo.

El código assembly `trade.s` sigue siendo la referencia mantener. Las otras cuatro variantes solo están en Python por ahora. El siguiente paso de evaluación debe contrastar robustez en otras series y costo de implementación antes de escoger la candidata final y sus aceleraciones.
