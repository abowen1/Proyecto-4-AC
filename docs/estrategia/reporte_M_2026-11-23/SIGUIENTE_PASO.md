# Evaluación pendiente de M1 a M5 en las recreadas

Estado al 23 de noviembre de 2026: existen dos etapas publicadas de M. M A/B/C perdió en las ocho series oficiales; M1–M5 ganó en esas mismas ocho. M3 tiene el mejor promedio de ese lote, pero no hay decisión final. **Ninguna de las cinco variantes M1–M5 ha sido ejecutada sobre las 70 recreadas en esta investigación.**

## Entradas para la próxima prueba

En el equipo local los 70 CSV están en `Proyecto/Totalidad Proyecto 4/series recreadas`, carpeta hermana de `Material de Canvas AC4` y `Desarrollo AC4`. Son 14 bloques por acción: META, AAPL, NFLX, AMD y TSLA. Cada CSV tiene columnas `tick,price` y 20.000 precios; son bloques consecutivos de observaciones existentes de 2022 a noviembre de 2024, sin solapamiento por acción según el índice.

Se adjunta una copia del [índice de las recreadas](datos/indice_recreadas_pendiente.json) con archivos, fechas y SHA256. **Los 70 CSV recreados no están incluidos en este paquete de publicación.** Para la prueba siguiente deben obtenerse desde esa carpeta o incorporarse de forma explícita; no reemplazarlos por las primeras reconstrucciones aproximadas de Tesla ni volver a interpolar precios.

## Configuraciones que se deben conservar

Usar `bandas/tools/m_bands.py` y las reglas de presupuesto, acumulación y liquidación de su `COMMON` y `BandPolicy`:

| Versión | Compra hasta | Vende desde | Presupuesto de exposición |
|---|---:|---:|---:|
| M1 | 120 | 210 | 100 % |
| M2 | 120 | 210 | 50 % |
| M3 | 110 | 210 | 100 % |
| M4 | 130 | 210 | 100 % |
| M5 | 120 | 230 | 100 % |

Capital inicial 10.000 por corrida, comisión 5 por orden ejecutada, máximo 63 por orden, ejecución al precio siguiente, sin deuda/cortos y sin liquidación final obligatoria. Los porcentajes limitan el presupuesto observado de entrada, no garantizan la exposición tras un salto de precio. No agregar un stop de patrimonio ni cambiar las bandas mientras se evalúa el lote.

## Resultado esperado del próximo trabajo

1. Verificar las 70 entradas contra el índice y conservar sus archivos y hashes.
2. Ejecutar las cinco configuraciones sin cambios: 350 corridas, reiniciando caja, inventario y estado en cada una.
3. Conservar trazas, caja, inventario, órdenes, comisiones, patrimonio y caída máxima. Reproducir la contabilidad con el testbench original.
4. Comparar por bloque y por acción, incluyendo pérdidas, posiciones abiertas al final y tiempos sin exposición.
5. Presentar las recreadas por separado de las ocho oficiales conocidas. Si se agrega una media conjunta, darle igual peso a cada serie e indicar que los períodos oficiales pueden coincidir con las recreadas.
6. Solo después discutir una selección o una nueva iteración. Cualquier ajuste posterior debe quedar como experimento distinto, sin sobrescribir esta referencia.

La elección de M no está trasladada a assembly/RTL. La estrategia vigente de la placa no se cambia automáticamente por estos resultados.
