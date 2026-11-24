# Ajuste anterior de X y luego Y

Historia del ajuste del 23/11/2026, entre M1–M5 y la [malla posterior de 15 candidatas](../malla_15/README.md). Todas las configuraciones usaron 100 % de presupuesto y los mismos ocho CSV oficiales. No son series nuevas ni una evaluación independiente.

1. Con Y = 210 se comparó X = 110, 120, 130, 140, 150. M110-210 lideró con media $18.283,625.
2. Se mantuvo X = 110 y se comparó Y = 190, 200, 210, 220, 230. M110-220 lideró con media $18.961,875.
3. Después se amplió a X = 105, 110, 115 y Y = 205, 210, 215, 220, 225: 15 variantes y 120 corridas adicionales. Se conserva por separado para no confundir selección sucesiva con validación independiente.

El criterio anterior fue mayor media final, luego mayor peor final, menor caída y umbral menor en caso de empate. Las dos etapas suman 80 evaluaciones, con 72 simulaciones distintas: los ocho casos de M110-210 se reutilizaron sin modificación en la segunda etapa.

## Compra X, venta fija 210

| Variante | Media final | Peor final | Comisión media |
|---|---:|---:|---:|
| M110-210 | $18.283,625 | $12.411 | $19,375 |
| M120-210 | $16.233,750 | $11.286 | $18,125 |
| M130-210 | $15.957,250 | $10.294 | $20,625 |
| M140-210 | $16.490,875 | $11.570 | $23,125 |
| M150-210 | $15.243,875 | $12.683 | $27,500 |

[Resultados por serie](01_X/resumen.csv) · [Configuraciones](01_X/casos_fijados.json) · [Validación contable](01_X/validacion_contabilidad.json)

## Compra fija 110, venta Y

| Variante | Media final | Peor final | Comisión media |
|---|---:|---:|---:|
| M110-190 | $17.413,250 | $12.411 | $19,375 |
| M110-200 | $17.966,750 | $12.411 | $19,375 |
| M110-210 | $18.283,625 | $12.411 | $19,375 |
| M110-220 | $18.961,875 | $12.411 | $19,375 |
| M110-230 | $16.909,500 | $12.411 | $16,250 |

[Resultados por serie](02_Y/resumen.csv) · [Configuraciones](02_Y/casos_fijados.json) · [Validación contable](02_Y/validacion_contabilidad.json)

[Protocolo](protocolo.json), [selección final de este lote](seleccion_final.json) y [verificación local](verificacion_iteracion.json). Esta carpeta conserva tablas y evidencia de las etapas intermedias; las trazas completas y el código reproducible de la malla final están en `../malla_15`. No se presenta esta evidencia intermedia como un ensayo adicional sobre datos desconocidos.
