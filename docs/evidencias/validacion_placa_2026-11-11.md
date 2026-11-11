# Base FPGA: compilación y comprobación física

Fecha: 11 de noviembre de 2026. Alcance: reparar herramientas, generar bitstreams y comprobar el programa original de botones/LED. No se eligió ni implementó una estrategia bursátil durante esta prueba.

## Resultado

- Yosys vuelve a iniciar y el flujo de compilación termina correctamente.
- `build/ac4.bin` generado con `sw/trade.hex` (mantener).
- `build/board_test.bin` generado con `sw/buttons_leds.hex`, el ejemplo original de Nicolás Villegas, y cargado en la Go Board.
- El programador terminó con `VERIFY OK` y CDONE alto.
- El usuario confirmó que los cuatro botones encienden y apagan sus respectivos LED al presionar y soltar.
- El usuario desconectó y reconectó USB y confirmó que los cuatro pares siguen funcionando, sin volver a programar.
- Se conservaron los 13 archivos RTL, los pines, el programa mínimo y el ejemplo de botones sin cambios. No se introdujo divisor de reloj ni optimización de microarquitectura.

## Reparación realizada

La instalación anterior de Yosys 0.69 dependía de `libtcl9.0.dylib`, ausente tras quedar instalado Tcl/Tk 9.1.0. Se reinstaló únicamente el paquete solicitado mediante Homebrew:

```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew reinstall yosys
```

Homebrew instaló Yosys 0.70 y su dependencia fmt 12.2.0. Se comprobó `yosys -V`: `Yosys 0.70+post`, revisión `0c11ea098be065e585a90a06e7b7da49936cf231`. No se hizo una actualización general de los paquetes ni se crearon enlaces artificiales entre versiones de Tcl.

Herramientas usadas: nextpnr-ice40 0.11.1_1, IceStorm/icepack/iceprog 1.1, Icarus Verilog/vvp 13.0. El modelo BRAM de las pruebas se volvió a tomar de la instalación de Yosys 0.70 y se repitieron las seis pruebas SPI de los dos programas y tres períodos: todas pasaron.

## Recursos y timing de ambas imágenes

| Métrica | Resultado |
|---|---:|
| Reloj implementado/objetivo | 25 MHz, directo |
| Fmax estimada después del ruteo | 44,808891 MHz |
| Celdas lógicas utilizadas | 1.082 / 1.280 |
| LUT4 reportadas por síntesis | 911 |
| BRAM utilizadas | 12 / 16 |
| Puertos físicos utilizados | 27 / 72 |
| Tamaño de cada bitstream | 32.220 bytes |

Las dos compilaciones dieron la misma utilización y estimación de frecuencia; difiere el contenido del programa. **No se cambió el reloj a 44,8 MHz**: esa cifra es la estimación del analizador para estas imágenes. La comprobación física descrita se hizo con el oscilador de 25 MHz.

No confundir las 1.082 celdas ocupadas con las 911 LUT4. Los recursos restantes tampoco garantizan que una extensión futura pueda colocarse y cerrar timing: se medirá cuando exista.

nextpnr reportó dos restricciones UART sin puerto correspondiente (`i_UART_RX` y `o_UART_TX`) en el PCF original. Se conservaron los archivos originales; el diseño actual no expone UART. No son fallos de los pines de botones/LED utilizados en esta prueba.

## Identificación y respaldo de la memoria

Al principio el dispositivo todavía no aparecía. Luego macOS reconoció el adaptador FTDI, pero `iceprog -t` devolvió identificación `FF FF FF FF`; lo mismo ocurrió a menor velocidad. El canal B no mostró control correcto de reset; se continuó con el canal A predeterminado.

No se escribió inmediatamente después de ese aviso. Una lectura de 512 bytes mostró datos no constantes y la cabecera iCE40 `7e aa 99 7e`. Se respaldaron los primeros 64 KiB y se compararon dos lecturas independientes, idénticas byte por byte. Esa región cubre el sector de 64 KiB que después borró el programador para escribir la prueba de 32.220 bytes.

SHA-256 del respaldo: `3bb68023bb65eedaa1093d689d2345b8b2e1c20f1aa9321b2b546a1609fca3d9`.

La consulta de identificación sigue sin dar un ID válido; no se estableció su causa. La lectura del contenido, la escritura, su verificación y el funcionamiento físico sí se comprobaron. No interpretar el código de salida cero de `iceprog -t` como prueba suficiente de identificación correcta.

El respaldo se conserva solo localmente en `build/flash_respaldo_antes_ac4.bin`, junto a la lectura de comprobación. No se publica su contenido. Para restaurar el estado previo de esa zona, si el usuario lo solicita, se puede programar ese respaldo.

## Archivos locales y reproducción

| Archivo local | Contenido |
|---|---|
| `build/ac4.bin` | Base con mantener; generado, no cargado en esta prueba |
| `build/board_test.bin` | Base con botones/LED; imagen que quedó cargada |
| `build/synthesis.log`, `build/timing.json` | Reportes de mantener |
| `build/board_test_synthesis.log`, `build/board_test_timing.json` | Reportes de botones/LED |
| `build/test_spi_yosys070.log` | Seis pruebas SPI repetidas con el modelo BRAM de Yosys 0.70 |
| `build/programacion_board_test.log` | Programación y `VERIFY OK` |
| `build/flash_respaldo_antes_ac4.bin` | Respaldo local anterior, 64 KiB |

SHA-256 de mantener: `adb2491e8f8eeea250e46070108de9d2cb4512f5454cf7fc35eb424d50885d27`.

SHA-256 de botones/LED: `1bb23ff0541e1d792ad12647e43548943d362c1bdcd50541b15931de264e99d2`.

`make build` reproduce la compilación de mantener. Para reproducir la de botones/LED, usar el mismo conjunto de fuentes, pines y parámetros, cambiando solo `MemFile` y escribiendo las salidas aparte:

```sh
yosys -l build/board_test_synthesis.log -p 'read_verilog rtl/*.v rtl/espino_core/*.v; chparam -set MemFile "sw/buttons_leds.hex" pochoco_soc; synth_ice40 -top pochoco_soc -json build/board_test.json; stat'
nextpnr-ice40 --hx1k --package vq100 --json build/board_test.json --pcf goboard.pcf --asc build/board_test.asc --freq 25 --report build/board_test_timing.json --log build/board_test_place_route.log
icepack build/board_test.asc build/board_test.bin
```

La programación realizada fue `iceprog build/board_test.bin`, después del respaldo. No se añadió un objetivo nuevo al Makefile ni se modificó código para esta prueba.

## Qué queda pendiente

- Validar recepción de precios y salida de decisiones por SPI físicamente, con un emisor/maestra apropiado. Aquí SPI se comprobó en simulación.
- Implementar y medir la estrategia que acuerde el equipo, con contabilidad y estado reales.
- Validar RAM de datos y el resto del comportamiento que utilice ese programa; botones/LED no certifica todas las rutas de Pochoco.
- Hacer las dos alternativas de hardware exigidas una vez medido el cuello de botella.

No se generaron series bursátiles nuevas ni se implementó el hard stop. La placa quedó con el ejemplo original de botones/LED, no con una estrategia de inversión.
