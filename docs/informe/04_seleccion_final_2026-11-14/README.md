# Selección final y carga de D en placa — 14 de noviembre de 2026

**Actualización del 17/11:** la serie oficial cambió a Meta. [Resultados vigentes](../05_meta_2026-11-17/README.md). Los números de este documento son históricos. `make test-final` usa ahora Meta por defecto; para reproducir este ensayo anterior usar `python3 tools/verify_canvas_final.py --series tb/practica.csv`. La nueva práctica no exige cambiar la imagen cargada.


## Decisión del equipo

Se elige **shifter acotado** como implementación final. La estrategia bursátil sigue siendo **D original: SMA32, banda 1, sin techo de retiro, comisión 5 y ejecución al precio siguiente**. QCAP queda como alternativa comparada para el informe. No se cambiaron el algoritmo, el RTL ni la imagen medida el 12/11.

| Variante | Promedio, 20.000 precios | Máximo observado | Celdas lógicas |
|---|---:|---:|---:|
| Software optimizado | 89,3779 ciclos | 802 | 1.091/1.280 |
| **Shifter elegido** | **64,2097 ciclos** | **257** | **1.202/1.280** |
| QCAP | 84,6320 ciclos | 791 | 1.186/1.280 |

La reducción de tiempo promedio del shifter es 28,16 %. No mejora la rentabilidad respecto de D en software: preserva decisiones y contabilidad, con más margen de tiempo. Todas las variantes funcionan a 25 MHz. Ver [comparación, perfiles, Amdahl, roofline y gráficos](../03_hardware_2026-11-12/README.md). Allí están también las pruebas previas de 20.000 precios, 2.000 en ronda rápida y extremos.

## Qué significa la maestra de Canvas

`tb/tb_proyecto_4.sv` emula la FPGA maestra **en simulación**: genera SCLK/MOSI/CS, recibe MISO y lleva la contabilidad. No envía esos pulsos a la Go Board conectada por USB. El USB permite programar la placa; esta imagen no implementa un puente USB/UART–SPI.

La copia del [enunciado](../../../material/enunciado/Proyecto_4_arq.pdf), página 1, dice que la FPGA maestra la opera el curso y estará disponible en la clase del **19/11** para pruebas. La sección 2.5 describe el testbench que la emula. Por tanto **no se exige que el grupo consiga una segunda placa**. La fecha citada corresponde a esa copia; revisar los avisos posteriores de Canvas antes de asistir.

La propuesta anterior de conseguir una maestra propia era una prueba adicional, no un requisito para avanzar. La conexión física se deja para la instancia del curso. No agregamos una maestra dentro del diseño ni almacenamos precios en el bitstream final.

## Verificación con el testbench de Canvas

`make test-final` configura una copia temporal del testbench para usar `sw/trade_shifter.s`, sin cambiar las tareas SPI, la contabilidad ni sus cuatro chequeos. Solo ajusta rutas/parámetros y quita el tipo `string` en dos `localparam` para compatibilidad con Icarus. Además compara cada orden recibida y cada estado de caja, acciones y patrimonio contra la referencia Python D.

La ejecución predeterminada usa 2.000 precios y T=100.000 ns, la ronda más rápida. Las salidas se guardan en `build/canvas_final/2000_100000/`; la copia archivada en `canvas/` registra el resultado de esta selección. Esta prueba ocurre en el Mac y no debe presentarse como una corrida física de precios.

Resultado: **4/4 chequeos aprobados**, 2.000 decisiones ejecutadas y estados contables coincidentes con Python. Patrimonio final **9.923**, 140 órdenes, 700 de comisiones y pérdida máxima 1.607. Este tramo de 2.000 no se debe confundir con la serie completa de 20.000, que finaliza en 17.909. El máximo que informa Canvas es **251 ciclos**, frente a 2.262 disponibles. El banco instrumental anterior registró 250 en ese tramo: son bancos con distinto arranque y medición por flancos; se conservan ambos resultados sin reetiquetar uno como el otro. El programa HEX es exactamente el mismo.

## Carga física realizada

Se respaldaron localmente 65.536 bytes de la flash y se comprobó que el programa, las fuentes RTL y la imagen coinciden con los hashes de la comparación anterior. Después se cargó **exactamente** `build/hardware/shifter/soc.bin`: 32.220 bytes. Iceprog terminó con **VERIFY OK y CDONE alto**. Los hashes y los registros de programación están en esta carpeta; el respaldo binario permanece local.

**La placa ya no tiene el diagnóstico A5: ahora tiene D con shifter.** No se debe esperar A5, B5 ni cuatro LED como señal de aprobación de este programa bursátil. El programa espera precios por los pines SPI. No se usaron los displays ni los LED como confirmación de una ronda real, porque aún no se han enviado precios físicos.

A5/B5 siguen siendo evidencia histórica de los autodiagnósticos de instrucciones: ambos pasaron después de programar y después de cortar alimentación. Ver [registro del 12/11](../03_hardware_2026-11-12/prueba_placa.md). La carga de hoy confirma la programación de flash; no certifica por sí sola una ejecución bursátil física.

## Reproducir la versión elegida

```sh
make test-final     # maestra simulada de Canvas + comparación Python por tick
make build-final    # D + shifter, imagen en build/hardware/shifter/soc.bin
make program-final  # programa la Go Board conectada, tras compilar esa variante
```

Los objetivos anteriores `build`/`program` conservan la referencia solo software para comparaciones; para la opción elegida usar los objetivos con sufijo `-final`. Se conservan `sw/trade.s` (referencia software) y `sw/trade_shifter.s` (selección final) sin sustituir uno por otro en esta etapa de pre-entrega.

## Próximo paso con el curso

Conectar a la maestra del curso y comprobar precios/respuestas, arranque y reinicio entre rondas. Confirmar en Canvas el procedimiento de inicio/reinicio y los parámetros definitivos. En una reconexión completa se reinicia el estado local; los botones no implementan un reinicio de ronda. Después registrar la evidencia real y seleccionar los archivos que irán a main junto con el informe. No publicar una prueba SPI física como aprobada antes de hacerla.
