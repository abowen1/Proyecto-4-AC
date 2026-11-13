# Instrumentación temporal de arranque

Esta carpeta no es una tercera alternativa para la competencia ni forma parte del área/rendimiento de A o B. Agrega una captura de la primera instrucción retirada y UART a 115.200 baudios nominales sobre el pin TX de la Go Board. Para hacer espacio se desconectan los displays. El programa y los controles de precio no utilizan esa UART.

La trama actual repetida es `55 AA 12 34` más la captura de 32 bits en orden de byte menos significativo primero. `DEADBEEF` indica que no se capturó el evento antes del timeout; no es un valor calculado por el ALU. `tools/read_trace_uart.py` solo lee datos y permite indicar puerto y baudios. Requiere pyserial para este diagnóstico, no para ensamblar ni simular las variantes finales.

Se utilizó para comparar arranque con reset de 15 y 63 ciclos. Las capturas antiguas de escritura x5 y con cabecera de un byte son experimentos previos, documentados por separado; no deben interpretarse con el formato actual. La instrumentación se probó aisladamente y dentro del SoC con `tb/tb_trace_uart.sv`.

El diagnóstico de cálculos que queda en la placa es A5, compilado con la variante normal `shifter`, sin UART ni esta instrumentación. El registro del hallazgo y sus límites está en `docs/informe/03_hardware_2026-11-12/diagnostico_arranque/`.
