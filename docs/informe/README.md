# Material para preparar el informe AC4

Esta carpeta conserva resultados, figuras y explicaciones del desarrollo, según lo solicitado por el equipo. Se publica en `pre-entrega`; el informe evaluado se preparará después.

- [01 · Perfil de D y ley de Amdahl](01_perfil_D_2026-11-12/README.md): mediciones por sección, código de medición, datos por precio e instrucción, gráficos PNG/SVG, predicciones y prioridades de optimización.
- [Reglas e implementación base de D](../estrategia/D_implementacion.md).
- [Evidencia previa de equivalencia D/Python](../evidencias/D_2026-11-12/).
- [Compilación y prueba física inicial](../evidencias/validacion_placa_2026-11-11.md).

Para las próximas variantes conservar en una carpeta propia: código o revisión exacta, comandos, configuración y hashes, mediciones originales, resultados resumidos, figuras PNG y SVG, interpretación y límites. Mantener separadas las predicciones de Amdahl de los speedups medidos. Registrar también los resultados que descarten una alternativa; sirven para justificar la elección final.

Las figuras se regeneran con herramientas de gráficos convencionales; no son capturas de una conversación. La referencia bursátil elegida sigue siendo D/SMA32/banda 1 sin techo de retiro. Comparar implementaciones de hardware manteniendo las mismas decisiones permite atribuir las diferencias de tiempo al hardware y al software que lo utiliza.
