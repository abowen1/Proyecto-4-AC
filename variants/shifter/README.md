# Alternativa shifter

Añade únicamente desplazamientos lógicos inmediatos: SLLI de 1, 5 y 6 posiciones, y SRLI de 1 posición. No implementa desplazamientos aritméticos ni por registro; el decodificador rechaza los demás desplazamientos.

Las fuentes en `rtl/` sustituyen por nombre los módulos correspondientes del núcleo base. El programa asociado es `sw/trade_m105_225_shifter.s`. Estas fuentes se compilan por separado de la versión final.

Pruebas de unidad y ejecución de instrucciones: `make test-hardware`. Equivalencia completa de esta implementación: `python3 tools/compare_m105_225_implementations.py --cases shifter`. Síntesis aislada: `python3 tools/hardware_variants.py shifter`.
