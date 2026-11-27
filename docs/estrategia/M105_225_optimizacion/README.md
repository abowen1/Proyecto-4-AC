# Implementaciones y mediciones M105-225

## Fuentes

| Caso | Assembly | ISA |
|---|---|---|
| Inicial MDIP | `sw/trade_m105_225.s` | Original |
| Software optimizado (versión final) | `sw/trade.s`, idéntico a `sw/trade_m105_225_soft.s` | Original |
| Shifter | `sw/trade_m105_225_shifter.s`, `variants/shifter/rtl/` | Shifter |
| QCAP | `sw/trade_m105_225_qcap.s`, `variants/qcap/rtl/` | QCAP |

Las rutas de fuentes se expresan respecto de la raíz del repositorio. La fundamentación de la elección se presenta en el [Informe Proyecto 4 AC](../../../informe/Informe_Proyecto_4_AC.pdf).

## Datos conservados

- `comparacion.csv`, `resumen.json`: recursos, timing, IC, ciclos, CPI y capacidad de servicio.
- `resultados_por_serie.csv`, `validacion_variantes.json`: equivalencia y perfiles de las cuatro implementaciones sobre 78 series.
- `mediciones_por_tick/`: 32 perfiles comprimidos de las ocho series oficiales y cuatro implementaciones.
- `compilacion/`: ensamblado, síntesis, place-and-route y resultados de las cuatro implementaciones y de la imagen final.
- `amdahl.csv`, `roofline.csv`: datos numéricos del análisis de rendimiento.
- `integracion_final.json`, `canvas_final.json`, `stress.json`, `validacion_publicacion.json` y registros de pruebas: comprobaciones conservadas.
- `imagen/`: imagen final y manifiesto; sus campos físicos reflejan el momento de generación. La validación física posterior se registra en `../../evidencia_fisica/`.
- `herramientas.json`, `fuentes_medicion_originales.json`: versiones y hashes históricos empleados en la medición, antes de reorganizar las rutas de entrega. Algunas herramientas de presentación citadas allí no forman parte de esta entrega.

El perfil cuenta instrucciones retiradas y ciclos de la ventana de servicio desde la recepción SPI hasta escribir la decisión; excluye la espera inactiva cuando se acelera la simulación. Se calcula a 25 MHz. La capacidad de servicio y los techos del modelo roofline no equivalen a la frecuencia efectiva de llegada de ticks.

## Repetición

`make measure` perfila Meta con el software final. `make compare-implementations` compara las cuatro implementaciones en las 78 series. `make build-final` sintetiza la selección final con comprobación de recursos y timing; no programa una placa. Todos los resultados nuevos van a `build/`.
