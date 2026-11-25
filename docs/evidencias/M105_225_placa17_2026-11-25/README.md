# Práctica física con la maestra — 25 de noviembre de 2026

Reporte confirmado por Andrés para el equipo. **Cinco ejecuciones, cuatro series oficiales distintas: tres primeros lugares, un segundo lugar y un tercer lugar.** Tesla enero 2022 se ejecutó dos veces, con la misma implementación y el mismo resultado de nuestro grupo.

## Identificación y versión

- **Hoy nuestro grupo fue la fila 7.** En la práctica anterior del miércoles fue la fila 6; la fila 6 de los podios de hoy corresponde a otro grupo.
- Placa: **Go Board 17**, identificada con plumón, no por un número de serie electrónico.
- Implementación: **M105-225, software optimizado e ISA original de Espino**, sin QCAP ni shifter. Se mantiene la misma estrategia e implementación en las ejecuciones reportadas.

## Podios de las ejecuciones documentadas

| Ejecución | Serie oficial | 1.º | 2.º | 3.º |
|---|---|---|---|---|
| 1 | Netflix enero 2022 | Fila 2: $13.098 | **Nuestro grupo, fila 7: $12.685** | Fila 6: $11.297 |
| 2 | AMD enero 2022 | **Nuestro grupo, fila 7: $32.555** | Fila 6: $29.250 | Fila 4: $17.622 |
| 3 | Tesla enero 2022 | **Nuestro grupo, fila 7: $21.659** | Fila 5: $21.224 | Fila 6: $18.260 |
| 4 | Tesla enero 2022, repetición | **Nuestro grupo, fila 7: $21.659** | Fila 5: $20.795 | Fila 6: $19.379 |
| 5 | Meta febrero 2022 | Fila 6: $23.215 | Fila 5: $22.682 | **Nuestro grupo, fila 7: $16.983** |

Meta se añadió tras revisar los videos que compartió Chapa. El número 5 identifica la quinta ejecución documentada; no fija su posición cronológica durante la práctica.

En Netflix quedamos **$413 por debajo del ganador** (3,15 % de su patrimonio) y $1.388 por encima del tercero. En AMD ganamos al segundo por **$3.305** (11,30 % de su patrimonio); en Tesla, por **$435** (2,05 %) y luego **$864** (4,15 %). En Meta quedamos terceros, **$5.699 por debajo del segundo** y **$6.232 por debajo del ganador**. Son diferencias frente a competidores, distintas del porcentaje frente a comprar y mantener.

El equipo informó que algunos competidores modificaron su estrategia antes de repetir Tesla. No se conoce qué cambiaron; no se atribuye el cambio de sus resultados a una causa técnica específica.

## Estado final confirmado de nuestro grupo

| Ejecución | Caja | Acciones | Órdenes ejecutadas totales | Patrimonio final | Ganancia sobre $10.000 |
|---|---:|---:|---:|---:|---:|
| Netflix | $89 | 94 | 2 | $12.685 | +$2.685 |
| AMD | $31 | 188 | 7 | $32.555 | +$22.555 |
| Tesla, primera ejecución | $21.659 | 0 | 4 | $21.659 | +$11.659 |
| Tesla, repetición | $21.659 | 0 | 4 | $21.659 | +$11.659 |
| Meta | $16.983 | 0 | 2 | $16.983 | +$6.983 |

La cifra confirmada de AMD es **188 acciones**. En Tesla se registran **cuatro órdenes totales**, no cuatro compras: la referencia simulada ejecuta dos compras y dos ventas. El desglose proviene de la simulación; el contador total y el estado final fueron confirmados por Andrés.

Los patrimonios, caja, inventario y número de órdenes coinciden exactamente con los [resultados previamente simulados](../../estrategia/M105_225_implementacion/resultados_78.csv) de las cuatro series distintas. En Meta, Andrés confirmó dos órdenes y cero acciones; por tanto, el patrimonio final es íntegramente caja. Esto confirma coincidencia del estado final observado, sin afirmar una captura física de todas las decisiones tick a tick.

Como referencia, los porcentajes recalculados sobre comprar y mantener de los CSV oficiales son **+38,20 % en Netflix**, **+291,52 % en AMD**, **+116,70 % en Tesla** y **+75,17 % en Meta**. Los valores aproximados relatados de la pantalla fueron +38,1 %, +291,5 %, +116,6 % y +75,1 %, respectivamente; se conservan ambas procedencias sin confundirlas.

## Comunicación y alimentación

El equipo confirmó que la placa se comunicó y funcionó correctamente con la maestra. Andrés desconectó la alimentación para transportarla y, al conectarla en la práctica, la implementación arrancó y operó: es evidencia de funcionamiento después de un corte de alimentación, aunque no se hizo una prueba específica adicional de desconexión/reconexión durante la práctica. El [registro del 24/11](../M105_225_placa17_2026-11-24/README.md) ya documentaba la verificación de la imagen tras reconectar USB.

No se detalló el mecanismo de reinicio entre cada ejecución ni se registraron mediciones físicas nuevas de latencia. No se modificaron código, configuración ni imagen para este reporte. Con esta actualización quedan documentados los resultados pendientes de la práctica; no se añaden pruebas físicas no realizadas.
