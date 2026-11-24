# Evaluación pendiente de las candidatas M X-Y

Estado al 23/11/2026: el recorrido publicado incluye M A/B/C, M1–M5, el ajuste sucesivo de X/Y y la malla de 15 variantes. La líder media del último lote es M105-220; el equipo aún no eligió una estrategia definitiva. **Las 15 variantes vigentes no se han probado en las 70 series recreadas.** Esta publicación no autoriza por sí sola a ejecutar el próximo experimento ni a cambiar el programa de la placa.

## Entradas para la próxima prueba

En el equipo local los 70 CSV están en `Proyecto/Totalidad Proyecto 4/series recreadas`, carpeta hermana de `Material de Canvas AC4` y `Desarrollo AC4`. Son 14 bloques por acción: META, AAPL, NFLX, AMD y TSLA. Cada CSV tiene columnas `tick,price` y 20.000 precios; son bloques consecutivos de observaciones existentes de 2022 a noviembre de 2024, sin solapamiento por acción según el índice.

Se adjunta una copia del [índice de las recreadas](datos/indice_recreadas_pendiente.json) con archivos, fechas y SHA256. **Los 70 CSV recreados no están incluidos en este paquete de publicación.** Para la prueba siguiente deben obtenerse desde esa carpeta o incorporarse de forma explícita; no reemplazarlos por las primeras reconstrucciones aproximadas de Tesla ni volver a interpolar precios.

## Configuraciones vigentes

La referencia actual está en [malla_15/protocolo.json](malla_15/protocolo.json): producto de X = 105, 110, 115 por Y = 205, 210, 215, 220, 225. Todas usan presupuesto del 100 %. Código en `malla_15/tools/m_bands.py`; ejecución de referencia en `malla_15/tools/compare_grid.py`. Las cinco M1–M5 permanecen como historia, no como el lote más reciente.

Capital inicial 10.000 por corrida, comisión 5 por orden ejecutada, máximo 63 por orden, ejecución al precio siguiente y sin venta final obligatoria. Mantener presupuesto, acumulación, liquidación enclavada y posibilidades de reentrada. No añadir stops ni elegir parámetros según nombre o fecha del archivo.

## Próxima evaluación, cuando el equipo la solicite

Si se conservan las 15 candidatas, 70 recreadas implican 1.050 corridas. Si el equipo reduce la selección antes de probarlas, fijar esa lista previamente y registrar el motivo. Conservar hashes, trazas, caja, inventario, órdenes, comisiones, patrimonio y caída porcentual; verificar la contabilidad original. Comparar por bloque y activo y mostrar por separado los resultados oficiales usados para ajustar. Algunos períodos oficiales pueden coincidir con las recreadas; no tratar todo el lote como datos independientes.

No trasladar automáticamente la selección a assembly/RTL. La placa requiere su propia implementación y validación después de decidir la estrategia.
