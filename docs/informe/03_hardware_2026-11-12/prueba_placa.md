# Prueba física: Go Board, 12 de noviembre de 2026

Estado final: **ambos autodiagnósticos de cálculo aprobados**. La placa queda con A5, diagnóstico del shifter acotado. La estrategia sigue siendo D; A5 identifica el hardware, no una estrategia bursátil distinta.

## Respaldo y programación

Antes de modificar la placa se leyeron 65.536 bytes. El prefijo coincide exactamente con el programa original de botones/LED que se había dejado en la placa. SHA256 del respaldo: `1efb1537bcf7dc567a9a0e3f0ac5aee6b38fa640cceb54bceaa8e7a2aa0a580d`. El binario de respaldo permanece local en `build/flash_antes_hardware_20261112.bin`.

Iceprog informa el ID de flash FF con una advertencia heredada; no se toma ese ID como validación. Se comprobó contenido real del respaldo y las programaciones terminaron con **VERIFY OK y CDONE alto**. Los hashes de las imágenes probadas están en `placa.json`.

## Hallazgo de arranque y corrección común

Con reset de 15 ciclos el usuario observó EE/E3; las lecturas de botones mostraron resultado 0 y esperado 8160. Hubo también un diagnóstico que pasó recién programado pero no tras quitar alimentación. Se registró la investigación sin dar esas pruebas por aprobadas.

La telemetría UART con cabecera completa detectó una primera instrucción distinta de la imagen. Con reset de 63 ciclos obtuvo `0x800000B7`, igual al HEX, tanto recién programada como tras quitar alimentación. Se aplicó esa espera a las tres implementaciones y se repitieron las simulaciones. El fenómeno eléctrico o de configuración exacto no se considera demostrado por estas pruebas; la modificación sí se comprobó en la placa.

## Confirmaciones del usuario

| Diseño | Tras programar | Tras desconectar y reconectar |
|---|---|---|
| Shifter acotado | A5, cuatro LED | A5, cuatro LED |
| QCAP | B5, cuatro LED | B5, cuatro LED |

Los programas no encienden los cuatro LED simplemente al arrancar: calculan resultados, comparan cada uno y solo llegan a A5/B5 si todas las comprobaciones pasan. El usuario confirmó las observaciones en el chat; no se adjuntan fotografías ni se afirma haberlas tomado.

Después se volvió a programar exactamente la imagen A5 ya validada; el programador confirmó VERIFY OK. El programa bursátil está compilado por separado en `build/hardware/shifter/soc.bin` y aún no se cargó para operar con una maestra.

## Alcance

Esta prueba valida configuración, arranque persistente y cálculos de instrucciones del procesador en la FPGA. **No valida todavía transacciones SPI físicas, todas las decisiones de 20.000 precios en la placa ni una ronda contra la maestra del curso.** Esas pruebas siguen pendientes. La equivalencia de las series completas y sus tiempos procede de simulaciones RTL con SPI y controles por tick.
