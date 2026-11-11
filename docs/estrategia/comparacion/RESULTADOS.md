# Comparación exploratoria de estrategias AC4

Caja inicial: 10.000. Comisión: 5 por orden ejecutada. Sin búsqueda de parámetros.

Señales enteras; orden calculada en n y ejecutada en n+1. No se modelan deadlines.

## Serie completa: 20.000 precios

| Estrategia | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Pérdida máxima desde peak |
|---|---:|---:|---:|---:|---:|
| Reversión a la media | 18502 | +8502 | 729 | 3645 | 5630 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |
| Medias móviles | 3817 | -6183 | 474 | 2370 | 8260 |
| Momentum | 2048 | -7952 | 597 | 2985 | 9526 |
| Regresión lineal | 90 | -9910 | 1264 | 6320 | 10495 |

## Primeros 2.000 precios: longitud predeterminada de Canvas

| Estrategia | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Pérdida máxima desde peak |
|---|---:|---:|---:|---:|---:|
| Reversión a la media | 10529 | +529 | 99 | 495 | 1968 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |
| Momentum | 7722 | -2278 | 105 | 525 | 3755 |
| Medias móviles | 6452 | -3548 | 79 | 395 | 5296 |
| Regresión lineal | 6400 | -3600 | 206 | 1030 | 4248 |

Benchmark oficial comprar y mantener: 6497 en la serie completa; 6695 en los primeros 2.000 precios.

El patrimonio incluye acciones al último precio. No se fuerza una venta final ni se ejecuta la última decisión pendiente.

Cada familia representa UNA variante y parámetros iniciales. El ranking puede cambiar con otra serie o parámetros. No hay estrategia elegida por el equipo ni validación de estas cuatro variantes en assembly/FPGA.

Reglas y límites: ../comparacion.md. Datos completos por tick: los diez CSV de esta carpeta. Reproducir con `make test-market compare` desde la raíz.
