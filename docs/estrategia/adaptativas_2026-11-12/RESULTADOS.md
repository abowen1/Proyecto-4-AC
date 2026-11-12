# A, D, DF, Ad y Dd: prueba del 12 de noviembre

Reglas fijadas antes de ejecutar; sin búsqueda automática de parámetros ni hard stop de patrimonio 20.000.

A conserva SMA32/banda 2; D SMA32/banda 1; DF es D con bloqueo de compras si SMA8 < SMA32. Ad usa SMA32 ± 1 desviación estándar poblacional; Dd ± 0,5. Los 32 precios incluyen el actual; igualdad y calentamiento mantienen. Las cantidades son las mismas en todas las candidatas, hasta 63 por orden.

## Datos y escala

TB_20000 utiliza toda la práctica original; TB_2000 sus primeros 2.000 puntos (valor predeterminado del TB). SPY, GOOGL y TSLA usan 502 cierres diarios reales, del 02-01-2024 al 31-12-2025. Los 250 cierres de 2023 se usan exclusivamente para calibrar una escala fija: precio = redondeo mitad hacia arriba(100 × cierre / máximo de 2023). No se usa el máximo/mínimo del período evaluado; no hay interpolación, repetición ni clipping. El escalado tiene la misma regla para los tres activos, pero un factor propio calculado con su pasado.

Fuentes: Yahoo Finance; respuestas originales JSON, hashes, URL y metadatos en raw/ y <símbolo>/fuente.json. Se usa close, no adjclose. No se añaden dividendos. Los precios convertidos son unidades del juego, no dólares: estos patrimonios no representan retornos de una inversión real. La cuantización, la comisión fija y el límite de cantidad afectan los resultados. Una ventana es 32 sesiones aquí; la unidad temporal de la práctica se desconoce. Esta comparación evalúa robustez en series distintas y no identifica la fuente original de Canvas.

## Resultados

### TB_20000

| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |
|---|---:|---:|---:|---:|---:|
| A | 18502 | +8502 | 729 | 3645 | 5630 |
| D | 17909 | +7909 | 1415 | 7075 | 7017 |
| DF | 16159 | +6159 | 525 | 2625 | 5167 |
| Dd | 12039 | +2039 | 1926 | 9630 | 8441 |
| Ad | 10352 | +352 | 1246 | 6230 | 4931 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |

Comprar y mantener ideal del enunciado: 6497. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.

### TB_2000

| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |
|---|---:|---:|---:|---:|---:|
| DF | 10723 | +723 | 69 | 345 | 1220 |
| A | 10529 | +529 | 99 | 495 | 1968 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |
| D | 9923 | -77 | 140 | 700 | 1607 |
| Dd | 9151 | -849 | 169 | 845 | 1727 |
| Ad | 9114 | -886 | 130 | 650 | 1861 |

Comprar y mantener ideal del enunciado: 6695. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.

### SPY

| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |
|---|---:|---:|---:|---:|---:|
| Ad | 11293 | +1293 | 23 | 115 | 1826 |
| Dd | 11207 | +1207 | 28 | 140 | 1921 |
| A | 11159 | +1159 | 21 | 105 | 1852 |
| D | 10822 | +822 | 26 | 130 | 1890 |
| DF | 10739 | +739 | 24 | 120 | 1869 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |

Comprar y mantener ideal del enunciado: 14395. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.

### GOOGL

| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |
|---|---:|---:|---:|---:|---:|
| Mantener | 10000 | +0 | 0 | 0 | 0 |
| A | 9969 | -31 | 26 | 130 | 2604 |
| Ad | 9355 | -645 | 13 | 65 | 2700 |
| Dd | 9243 | -757 | 21 | 105 | 2524 |
| D | 9032 | -968 | 28 | 140 | 2857 |
| DF | 9032 | -968 | 28 | 140 | 2857 |

Comprar y mantener ideal del enunciado: 22418. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.

### TSLA

| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |
|---|---:|---:|---:|---:|---:|
| DF | 14635 | +4635 | 31 | 155 | 2134 |
| Dd | 13636 | +3636 | 53 | 265 | 6546 |
| D | 12858 | +2858 | 67 | 335 | 6647 |
| A | 11856 | +1856 | 56 | 280 | 6393 |
| Ad | 11717 | +1717 | 37 | 185 | 6409 |
| Mantener | 10000 | +0 | 0 | 0 | 0 |

Comprar y mantener ideal del enunciado: 17951. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.

## Exactitud y límites

Caja inicial 10.000, comisión 5 por orden ejecutada, sin deuda/cortos, ejecución de la decisión al precio siguiente. El último patrimonio incluye inventario; no se fuerza venta final ni se ejecuta la última decisión pendiente. Se reproduce cada tick con la tarea ejecutar original de Canvas, incluidos casos límite. A/D/DF del TB completo deben coincidir byte por byte con las trazas previas.

Ad/Dd comparan (b × (S − Np))² > a² × (NQ − S²), donde S=sum(precios), Q=sum(precios²), N=32 y k=a/b. El signo de S−Np decide compra/venta. No requieren raíz ni división en la referencia, pero sí multiplicaciones y atención al ancho de los intermedios. Aún no están implementadas en Espino ni validadas en tiempo. No asumir costo equivalente a A/D.

Exploración: mirar estos resultados deja de reservar estos períodos como prueba final independiente. No elegir una variante solo porque gana en esta práctica conocida. Conviene comprobar después otros períodos separados antes de cerrar la selección.

Reproducir desde la raíz: `python3 tools/compare_adaptive.py`. Requiere Python estándar, iverilog y vvp; los JSON ya están archivados, sin descarga nueva.
