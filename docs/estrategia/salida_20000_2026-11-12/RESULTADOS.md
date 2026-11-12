# Salida permanente al alcanzar patrimonio 20.000

Regla fijada antes de correr: al observar caja + acciones*precio >=20.000 después de ejecutar la orden pendiente, activar salida permanente. Desde esa decisión se venden hasta 63 acciones por tick al precio siguiente, aun si rebota o cae durante la liquidación. Cuando no quedan acciones, mantener efectivo para siempre. Si no llega al objetivo, seguir con la estrategia base. No se conoce el final de la serie para tomar decisiones.

No equivale a retirar exactamente 20.000: puede venderse por menos o por más, y hay comisiones. Si se dispara en el último tick no hay tiempo de ejecutar la venta. No se vende todo en un único tick cuando hay más de 63 acciones. No se agregó al programa Espino ni a los resultados anteriores.

Datos: TB original completo y las seis series largas de 2.000 sesiones. Estas últimas usan escala al máximo del tramo completo y contienen información futura en el preprocesamiento; son exploratorias, no prueba final independiente. Se conserva el capital entre años dentro de cada corrida; cada activo y variante empieza con 10.000.

## TB_20000

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 18502 | 18502 | +0 | no |  |  |  |  |
| D | 17909 | 19902 | +1993 | sí | 11757 |  | 20025 | 19902 |
| DF | 16159 | 20050 | +3891 | sí | 12335 |  | 20111 | 20050 |

## SPY

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 14098 | 14098 | +0 | no |  |  |  |  |
| D | 14723 | 14723 | +0 | no |  |  |  |  |
| DF | 14488 | 14488 | +0 | no |  |  |  |  |

## GOOGL

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 17509 | 17509 | +0 | no |  |  |  |  |
| D | 23180 | 20216 | -2964 | sí | 1433 | 2023-09-28 | 20161 | 20216 |
| DF | 14977 | 14977 | +0 | no |  |  |  |  |

## TSLA

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 11374 | 21669 | +10295 | sí | 715 | 2020-11-18 | 21005 | 21669 |
| D | 15282 | 21819 | +6537 | sí | 562 | 2020-04-14 | 21221 | 21819 |
| DF | 7042 | 7042 | +0 | no |  |  |  |  |

## TSM

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 13648 | 13648 | +0 | no |  |  |  |  |
| D | 10013 | 10013 | +0 | no |  |  |  |  |
| DF | 11361 | 11361 | +0 | no |  |  |  |  |

## NVDA

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 27375 | 20044 | -7331 | sí | 1673 | 2024-09-12 | 20084 | 20044 |
| D | 48655 | 20308 | -28347 | sí | 842 | 2021-05-24 | 20207 | 20308 |
| DF | 18028 | 18028 | +0 | no |  |  |  |  |

## INTC

| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |
|---|---:|---:|---:|---|---:|---|---:|---:|
| A | 16272 | 16272 | +0 | no |  |  |  |  |
| D | 11458 | 11458 | +0 | no |  |  |  |  |
| DF | 11510 | 11510 | +0 | no |  |  |  |  |

## Validación y reproducción

Las bases se contrastan con cada tick de sus trazas anteriores. Si no se activa el objetivo, la traza debe ser idéntica. Las 42 corridas completas más 20 casos límite se verifican con la tarea contable original de Canvas (192.020 ticks). Ver configuración, resumen, trazas y validacion_contabilidad.json.

Reproducir: `python3 tools/compare_target_exit.py`. Requiere los lotes ya archivados, Python estándar, iverilog y vvp.
