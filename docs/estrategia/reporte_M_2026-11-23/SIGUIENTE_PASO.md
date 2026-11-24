# Siguiente paso: prueba física de M105-225

Las etapas 1-3 de implementación/equivalencia/integración y 4-5 de medición/optimización/generación de imagen están completas. Se eligió software optimizado en ISA base después de comparar shifter y QCAP; la mejora media es 19,73% con idénticas decisiones.

- [Reporte técnico e imagen](../M105_225_optimizacion/README.md).
- [Decisión financiera](../seleccion_M105_225_2026-11-24/README.md).
- [Validación funcional](../M105_225_implementacion/README.md).

La FPGA no se programó. El trabajo está en pausa antes de conectar/programar la placa, comprobar arranque y transacciones SPI físicas y probar la maestra del curso. `make build-final` genera la imagen; `make program-final` solo se debe ejecutar cuando corresponda esa etapa. No cambiar las bandas financieras durante una validación de hardware.
