# A, D y DF: 2.000 sesiones por activo

18 corridas sobre las mismas 2000 sesiones diarias comunes: 2018-01-18 a 2025-12-31. Activos: SPY, GOOGL, TSLA, TSM (ADR de TSMC), NVDA e INTC. Sin repetir ni interpolar observaciones. Fuentes Yahoo Finance y JSON originales archivados con hashes.

## Qué significa 2.000 frente a 20.000

El TB de Canvas tiene NTICKS=2000 por defecto; practica.csv tiene 20000 precios. Este lote iguala el número de puntos predeterminado, no la serie completa. Un tick es un precio recibido: no establece una duración de mercado. Aquí cada punto es un cierre diario; son casi ocho años. No equiparar 2000 días a 2000 transacciones de bolsa, ni a los períodos físicos de SPI de 10/1/0,1 ms.

## Escala y alcance de la prueba

La regla se fija antes de ejecutar las estrategias: precio = round_half_up(255 × cierre / máximo del tramo completo), independiente para cada activo. Misma regla para los seis. Preserva proporcionalidad salvo cuantización, sin desplazar el mínimo, sin logaritmos y sin clipping. Se usa close en la base por acción provista por Yahoo (splits ajustados), sin añadir dividendos. Los JSON completos descargados comienzan en 2016; solo se usan las últimas 2000 fechas comunes hasta el final de 2025.

**La preparación de precios usa el máximo futuro de todo el tramo.** No es calibración con un año previo ni validación fuera de muestra. Se eligió esta normalización para alojar recorridos de hasta unas 65 veces entre mínimo y máximo (NVDA) en 1–255 sin saturarlos. No se buscaron factores que maximizaran resultados. Cada señal usa solo los precios normalizados actuales/pasados, pero la escala sí conoce el futuro y puede modificar las decisiones: estos resultados son exploratorios del juego, no un backtest financiero causal de punta a punta.

La resolución de un byte pierde movimientos pequeños, especialmente en los primeros años de acciones que luego crecieron mucho. Los contadores adjacent_unchanged y rangos están en fuente.json. Los patrimonios no representan dólares reales ni se comparan directamente con los lotes a nivel 50/100. Ampliar la longitud no corrige estos límites, no garantiza más operaciones ni demuestra generalización a la serie desconocida de presentación.

## Reglas conservadas

A: SMA32, banda 2. D: SMA32, banda 1. DF: D más bloqueo de compras cuando SMA8 < SMA32; ventas sin cambios. Igualdad mantiene, promedio incluye precio actual, 31 ticks iniciales sin señal. Cantidades máximas 63 por orden; caja inicial 10000, comisión 5 por orden ejecutada, sin deuda/cortos, ejecución al precio siguiente, sin venta final forzada ni hard stop de patrimonio 20000. No se reinicia caja/inventario entre años. Solo se ejecutan las primeras 1999 decisiones propuestas.

## SPY

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| D | 14723 | +4723 | 136 | 680 | 3468 |
| DF | 14488 | +4488 | 102 | 510 | 3366 |
| A | 14098 | +4098 | 102 | 510 | 3332 |

Comprar y mantener ideal del enunciado: 24448. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## GOOGL

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| D | 23180 | +13180 | 237 | 1185 | 6258 |
| A | 17509 | +7509 | 155 | 775 | 4570 |
| DF | 14977 | +4977 | 131 | 655 | 4559 |

Comprar y mantener ideal del enunciado: 54839. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## TSLA

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| D | 15282 | +5282 | 322 | 1610 | 20186 |
| A | 11374 | +1374 | 160 | 800 | 15590 |
| DF | 7042 | -2958 | 80 | 400 | 6969 |

Comprar y mantener ideal del enunciado: 194699. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## TSM

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| A | 13648 | +3648 | 140 | 700 | 6736 |
| DF | 11361 | +1361 | 107 | 535 | 4922 |
| D | 10013 | +13 | 173 | 865 | 5151 |

Comprar y mantener ideal del enunciado: 67505. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## NVDA

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| D | 48655 | +38655 | 374 | 1870 | 11804 |
| A | 27375 | +17375 | 157 | 785 | 7815 |
| DF | 18028 | +8028 | 78 | 390 | 5520 |

Comprar y mantener ideal del enunciado: 328216. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## INTC

| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |
|---|---:|---:|---:|---:|---:|
| A | 16272 | +6272 | 159 | 795 | 7118 |
| DF | 11510 | +1510 | 127 | 635 | 6528 |
| D | 11458 | +1458 | 185 | 925 | 7938 |

Comprar y mantener ideal del enunciado: 8255. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.

## Validación y reproducción

Las 18 trazas completas se reproducen con la tarea contable original de Canvas, comprobando caja, acciones, patrimonio, órdenes y caída por tick, más 20 casos límite: 36020 comparaciones. No se valida ejecución de A/D/DF en Espino ni deadlines. Los lotes anteriores quedan conservados. Estos activos comparten fechas y varios pertenecen al mismo sector; no son experimentos independientes.

Reproducir desde la raíz: `python3 tools/compare_long_history.py`. Usa JSON archivados, Python estándar, iverilog y vvp. La referencia ideal se incluye para contexto, no se mezcla con las tres candidatas.
