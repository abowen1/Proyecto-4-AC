# Estado de la estrategia

Fecha: 11 de noviembre de 2026.

Estado: pendiente de propuesta de la Coni y selección del equipo. Hay una comparación exploratoria de cuatro variantes sugeridas por el enunciado más mantener, implementadas en Python. Las reglas y resultados están en `comparacion.md` y `comparacion/RESULTADOS.md`. No representan una elección final.

El programa `sw/trade.s` solo mantiene. El diagnóstico SPI tampoco toma decisiones bursátiles. Las cuatro variantes bursátiles todavía no están implementadas en assembly ni validadas en FPGA.

Cuando haya una candidata, registrar reglas exactas, parámetros, memoria, redondeos, estado inicial y tratamiento de casos límite. Entregar referencia ejecutable y decisiones por tick para comprobar equivalencia con Espino. Reproducir ejecución al precio siguiente, comisión, límites de caja e inventario.

No depende de esta elección: preparación de Pochoco, recepción SPI, arranque, mediciones y pruebas de protocolo.

Sí depende: estado del algoritmo, operaciones costosas, implementación final en assembly y selección de las dos alternativas de aceleración.
