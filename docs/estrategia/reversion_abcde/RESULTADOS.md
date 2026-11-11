# Reversión A, B, C, D y E

Mismos 20.000 precios, caja inicial 10.000 y comisión 5. Parámetros seleccionados antes de correr este lote, cambiando una variable por vez respecto de A.

| Variante | Ventana (ticks) | Banda (precio) | Patrimonio final | Órdenes | Comisiones | Drawdown máximo |
|---|---:|---:|---:|---:|---:|---:|
| Reversión A | 32 | 2 | 18502 | 729 | 3645 | 5630 |
| Reversión B | 16 | 2 | 13983 | 676 | 3380 | 5375 |
| Reversión C | 64 | 2 | 14193 | 524 | 2620 | 6629 |
| Reversión D | 32 | 1 | 17909 | 1415 | 7075 | 7017 |
| Reversión E | 32 | 4 | 8559 | 148 | 740 | 6123 |

A conserva exactamente la variante original. B/C cambian solo la ventana; D/E cambian solo la banda.

Compra cuando promedio − precio > banda; vende cuando promedio − precio < −banda; dentro de la banda mantiene la posición. La ventana incluye el precio actual. Espera a llenar la ventana antes de operar. Se usan comparaciones enteras sin redondear el promedio.

Se mantiene el desfase de un precio y la misma política de cantidades que en la primera comparación. Los montos ya incluyen comisiones y valoran acciones remanentes al precio final. No hay ventas en corto, deuda ni liquidación forzada al terminar.

La contabilidad se compara por tick con la tarea original de Canvas. Esto no implementa las variantes en assembly ni mide si cumplen el plazo. Todas usan la misma serie conocida: una ganadora aquí no demuestra que lo sea en otras series.

Reproducir: `make compare-reversion`. No se sobrescriben los resultados del lote anterior.
