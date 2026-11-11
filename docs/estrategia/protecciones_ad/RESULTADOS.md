# A/D: pánico, filtro y exposición

Mismos 20.000 precios, capital 10.000, comisión 5 y desfase de ejecución de un tick. A/D coinciden exactamente con las corridas anteriores.

| Variante | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| A | 18502 | +8502 | 729 | 3645 | 5630 |
| D | 17909 | +7909 | 1415 | 7075 | 7017 |
| AP | 10939 | +939 | 592 | 2960 | 5275 |
| DP | 8887 | -1113 | 1175 | 5875 | 5539 |
| AF | 10002 | +2 | 106 | 530 | 3186 |
| DF | 16159 | +6159 | 525 | 2625 | 5167 |
| AE | 9612 | -388 | 922 | 4610 | 3141 |
| DE | 7786 | -2214 | 1544 | 7720 | 3517 |

## Reglas elegidas antes de correr este lote

- A: SMA32, banda 2; D: SMA32, banda 1. Se mantienen reglas originales de señales y cantidades.
- AP/DP: caída de al menos 10% desde el máximo del precio observado durante una posición con inventario. Liquida en órdenes sucesivas de hasta 63, sin recomprar durante la liquidación. Después de quedar sin acciones, espera 32 ticks completos antes de habilitar otra compra. El máximo se reinicia al quedar sin acciones. El disparo no compara patrimonio ni precio medio de compra.
- AF/DF: bloquea nuevas compras cuando SMA8 < SMA32. No fuerza ventas: las ventas siguen la señal base. Los promedios incluyen el último precio.
- AE/DE: objetivo de exposición máximo 50% del patrimonio al precio observado. Calcula acciones objetivo como floor((patrimonio − comisión)/(2 × precio)). Limita nuevas compras y vende excesos en órdenes de hasta 63. El precio siguiente y el límite por orden pueden impedir cumplir el 50% de inmediato. La corrección puede generar ventas pequeñas y más comisiones.
- Cada protección se aplica por separado; ninguna variante mezcla P/F/E. Pánico incluye espera para evitar recomprar inmediatamente después de liquidar; no se buscó el mejor porcentaje ni la mejor espera.

## Validación y límites

Las órdenes de las ocho variantes se reprodujeron con la tarea contable exacta de Canvas, comparando caja, acciones, patrimonio, órdenes y drawdown por tick. A/D se contrastaron con sus trazas anteriores. No son implementaciones en Espino ni resultados de plazos de hardware.

El riesgo se mide aquí como caída absoluta máxima desde un máximo anterior de patrimonio, no como porcentaje. El patrimonio final incluye acciones valoradas al último precio; no se fuerza liquidación final.

Reproducir con `make compare-protections`. Se mantienen los lotes anteriores. Evaluación exploratoria sobre la misma serie conocida; sin búsqueda automática de parámetros ni validación en otra serie.
