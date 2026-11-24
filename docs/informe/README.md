# Material para preparar el informe AC4

**Estado 24/11: M105-225 elegida.** [Reporte de selección y evidencia](../estrategia/seleccion_M105_225_2026-11-24/README.md) con 78 series, 312 evaluaciones y el PDF compacto. La incorporación a Espino/RTL y su prueba física siguen pendientes; el material de D se conserva como historia y como infraestructura reutilizable.

Esta carpeta conserva resultados, figuras y explicaciones del desarrollo, según lo solicitado por el equipo. Se publica en `pre-entrega`; el informe evaluado se preparará después.

- [01 · Perfil de D y ley de Amdahl](01_perfil_D_2026-11-12/README.md): mediciones por sección, código de medición, datos por precio e instrucción, gráficos PNG/SVG, predicciones y prioridades de optimización.
- [02 · Vía rápida de 63, implementada y conservada](02_via_rapida_63_2026-11-12/README.md): equivalencia en 22.816 precios, reducción de tiempo promedio 26,33% en la práctica completa, perfil nuevo, regresiones individuales y ambos programas conservados.
- [03 · Dos alternativas de hardware y validación física](03_hardware_2026-11-12/README.md): shifter acotado y QCAP, comparación contra software, recursos/Fmax, Amdahl, Ops/s, roofline, autodiagnósticos A5/B5 y corrección de arranque común comprobada al reconectar.
- [Reglas e implementación base de D](../estrategia/D_implementacion.md).
- [Evidencia previa de equivalencia D/Python](../evidencias/D_2026-11-12/).
- [Compilación y prueba física inicial](../evidencias/validacion_placa_2026-11-11.md).

Para las próximas variantes conservar en una carpeta propia: código o revisión exacta, comandos, configuración y hashes, mediciones originales, resultados resumidos, figuras PNG y SVG, interpretación y límites. Mantener separadas las predicciones de Amdahl de los speedups medidos. Registrar también los resultados que descarten una alternativa; sirven para justificar la elección final.

Las figuras se regeneran con herramientas de gráficos convencionales; no son capturas de una conversación. La referencia de las mediciones históricas siguientes es D/SMA32/banda 1; desde el 24/11 la estrategia bursátil seleccionada es M105-225 y sus mediciones de implementación están pendientes. Comparar implementaciones de hardware manteniendo las mismas decisiones permite atribuir las diferencias de tiempo al hardware y al software que lo utiliza.

- [04 · Selección final D/shifter y carga en placa](04_seleccion_final_2026-11-14/README.md): decisión confirmada, maestra simulada de Canvas, programación física y alcance pendiente con la maestra del curso.

- [05 · Nueva práctica oficial Meta](05_meta_2026-11-17/README.md): D pierde frente a ambas referencias, equivalencia completa de tres implementaciones, ronda rápida Canvas aprobada y métricas/gráficos actualizados.

- [Reporte M del 23/11](../estrategia/reporte_M_2026-11-23/README.md): historia desde A/B/C y M1–M5, ajuste sucesivo X/Y y [malla vigente de 15 candidatas](../estrategia/reporte_M_2026-11-23/malla_15/README.md). Ocho gráficos, 120 corridas, parámetros, comisiones, caídas y trazas reproducibles para fundamentar la elección final. Este registro conserva la etapa previa. El 24/11 se eligió M105-225 tras evaluar cuatro finalistas sobre 78 series; ver el reporte vigente enlazado arriba.
