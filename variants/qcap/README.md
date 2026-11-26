# Alternativa qcap

Añade la instrucción custom `qcap`: devuelve `min(63, presupuesto_unsigned / precio_unsigned_low8)`. El RTL define también su comportamiento para precio cero; no es una división general de RV32M.

Las fuentes en `rtl/` sustituyen por nombre los módulos correspondientes del núcleo base. El programa asociado es `sw/trade_m105_225_qcap.s`. Estas fuentes se compilan por separado de la versión final.

Pruebas de unidad y ejecución de instrucciones: `make test-hardware`. Equivalencia completa de esta implementación: `python3 tools/compare_m105_225_implementations.py --cases qcap`. Síntesis aislada: `python3 tools/hardware_variants.py qcap`.
