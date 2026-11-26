# Alternativa shifter

Añade desplazamientos lógicos y aritméticos (registro e inmediato) en la ALU y su decodificación.

Las fuentes en `rtl/` sustituyen por nombre los módulos correspondientes del núcleo base. El programa asociado es `sw/trade_m105_225_shifter.s`. Estas fuentes se compilan por separado de la versión final.

Pruebas de unidad y ejecución de instrucciones: `make test-hardware`. Equivalencia completa de esta implementación: `python3 tools/compare_m105_225_implementations.py --cases shifter`. Síntesis aislada: `python3 tools/hardware_variants.py shifter`.
