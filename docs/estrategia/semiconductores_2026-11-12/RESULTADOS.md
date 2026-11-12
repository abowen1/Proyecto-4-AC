# A, D y DF: TSMC, NVIDIA e Intel

18 corridas: TSM/NVDA/INTC y controles SPY/GOOGL/TSLA. Solo A, D y DF. Sin búsqueda de parámetros, variantes nuevas ni hard stop en 20.000.

## Protocolo y cambio de escala

Se usan 502 cierres diarios por activo (02-01-2024 a 31-12-2025). Calibración: 250 cierres de 2023. TSM es el ADR estadounidense de TSMC. Fuente Yahoo Finance, campo close (histórico provisto con ajustes por splits; no adjclose ni pagos de dividendos). JSON originales, URL, hashes y precios convertidos archivados. El split 10:1 de NVDA en junio de 2024 no se interpreta como un desplome de precio: el proveedor expresa el histórico en la misma base por acción. Referencia del evento: https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2025/

Con la regla anterior, 100*cierre/máximo_2023, TSM llegaría a 289 y NVDA a 411: no caben en 1–255. Este lote usa round_half_up(50*cierre/máximo_2023) para TODOS los activos, sin clipping, repetir ni interpolar datos. El cambio de nivel se decidió después de inspeccionar los rangos de datos, para admitirlos en el protocolo; no se probaron niveles para escoger el de mayor patrimonio. La transformación de cada tick usa solo su precio y una constante calculada con 2023.

La escala no es inocua: cambia la banda relativa de las estrategias, los redondeos, el inventario y las comisiones relativas. Por eso se repitieron también SPY/GOOGL/TSLA con nivel 50. Comparar dentro de este lote; no mezclar sus cifras con las de nivel 100. Ambos lotes se conservan. Los patrimonios son unidades del juego, no dólares ni retornos financieros reales.

A: SMA32/banda 2. D: SMA32/banda 1. DF: D más filtro que bloquea compras si SMA8 < SMA32; no fuerza ventas. Media incluye el último precio, calentamiento 32, desigualdad estricta. Caja 10.000, comisión 5 por orden efectiva, cantidades hasta 63, no cortos/deuda, orden ejecutada al precio siguiente. Sin liquidación final. Los parámetros de las tres candidatas son los mismos de los lotes previos.

## TSM

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| DF | 13171 | +3171 | 43 | 215 | 2243 |
| D | 12654 | +2654 | 50 | 250 | 4331 |
| A | 11872 | +1872 | 38 | 190 | 4124 |

Benchmark ideal comprar y mantener: 29923. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## NVDA

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| D | 16448 | +6448 | 57 | 285 | 4851 |
| A | 16237 | +6237 | 46 | 230 | 4781 |
| DF | 14304 | +4304 | 37 | 185 | 4320 |

Benchmark ideal comprar y mantener: 38491. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## INTC

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| A | 17093 | +7093 | 81 | 405 | 3615 |
| D | 15483 | +5483 | 119 | 595 | 4258 |
| DF | 10613 | +613 | 16 | 80 | 917 |

Benchmark ideal comprar y mantener: 7663. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## SPY

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| A | 11951 | +1951 | 15 | 75 | 1520 |
| D | 11330 | +1330 | 33 | 165 | 1811 |
| DF | 10580 | +580 | 10 | 50 | 252 |

Benchmark ideal comprar y mantener: 14373. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## GOOGL

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| DF | 10287 | +287 | 20 | 100 | 1890 |
| D | 10062 | +62 | 35 | 175 | 2484 |
| A | 9917 | -83 | 25 | 125 | 2580 |

Benchmark ideal comprar y mantener: 22581. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## TSLA

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |
|---|---:|---:|---:|---:|---:|
| DF | 12831 | +2831 | 26 | 130 | 1323 |
| A | 12290 | +2290 | 60 | 300 | 6457 |
| D | 12044 | +2044 | 74 | 370 | 5934 |

Benchmark ideal comprar y mantener: 18290. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.

## Validación y límites

Cada decisión se reprodujo con la tarea contable original de Canvas. Se verifican caja, acciones, patrimonio, órdenes y caída máxima en cada tick; se añaden 20 casos límite. Ver validacion_contabilidad.json. No se ejecutaron las estrategias en Espino ni se midieron deadlines. Los datos y reglas de los lotes anteriores se conservan.

Los tres activos nuevos pertenecen al mismo sector y las seis pruebas usan el mismo período: no son seis experimentos de mercado independientes. La escala cambia respecto del primer lote y estos períodos ya están explorados; todavía no hay prueba final reservada ni selección definitiva de estrategia.

Reproducir: `python3 tools/compare_semiconductors.py` desde la raíz. Python estándar, iverilog y vvp; utiliza los JSON archivados sin descargar de nuevo.
