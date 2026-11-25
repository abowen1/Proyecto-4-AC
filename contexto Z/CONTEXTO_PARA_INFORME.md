# Familia Z: del momentum con protecciones al sistema M

## Nombres y origen

En el informe se utiliza **Z**. Los archivos originales dicen Baltazar o Baltasar; Paciente y Lento son sus variantes. Mantener estos nombres como equivalencias evita confundir Z con las estrategias A–E anteriores o con M105-225.

Z surgió tras el desempeño desfavorable de D en las nuevas series oficiales. La inspiración conceptual fue otra competencia con momentum, exposición limitada, take profit y stop loss. Se trasladó ese espíritu al mercado del proyecto, **sin noticias, sin señales externas y sin información sobre compras o ventas de otros grupos**. Las comisiones y reglas oficiales no se alteraron para mejorar los resultados.

## Qué hacía Z

La familia principal seguía momentum: comparaba el precio actual con uno anterior y compraba después de detectar una subida suficiente. El control inicial utilizaba cinco intervalos y un umbral de 0,8 %. Se exploraron límites de exposición de 100 %, 50 % y 15 %, y mecanismos de stop loss, toma de ganancias y trailing.

La gestión permitía una posición con **una sola orden de entrada**, hasta 63 acciones, sin seguir acumulando antes de cerrar. El límite de exposición se aplicaba a la nueva entrada según el precio observado; no era un rebalanceo permanente. Una orden decidida ahora se ejecutaba al precio del tick siguiente, recortada por caja o inventario. No se garantizaba salir exactamente al precio del stop.

Las salidas se evaluaban contra el costo real de entrada, incluida la comisión de compra, y el valor de liquidación neto de la comisión de venta. Podían activarse por señal contraria, stop, take profit o trailing; después de vender se imponía una espera para reentrar.

**Z no era el sistema de bandas absolutas de M.** Sus umbrales porcentuales se referían al movimiento reciente, al costo de la posición o a su máximo. También hubo un control experimental que conservaba la señal de D y le aplicaba la gestión de Z; no debe describirse como el mecanismo de entrada de toda la familia.

## Iteraciones para reducir operaciones y comisiones

La segunda etapa probó aumentar el tiempo de espera, exigir movimientos más persistentes y confirmados, ampliar los umbrales de salida y eliminar algunas salidas por señal. Los parámetros se conservan íntegros en `02_reduccion_comisiones/plan.json` y `tools/baltazar.py` de esa etapa.

| Código histórico | Cambio principal |
|---|---|
| B0_original | Control: momentum 5 > 0,8 %, exposición 50 %, TP/SL 1,5 %, espera 8. |
| B1_espera | Solo aumenta la espera posterior a una venta, de 8 a 64 ticks. |
| B2_momentum | Momentum 32 > 2 %, con tres confirmaciones. |
| B3_salidas | Amplía TP a 4 % y SL a 3 %; mantiene salida por momentum corto. |
| B4_solo_TP_SL | B3 sin salida por momentum contrario. |
| B5_persistente | Combina momentum persistente, espera 64, TP 4 % y SL 3 %; mínimo 32 ticks para salir por señal. |
| B6_paciente | Sustituye el TP fijo de B5 por trailing 3 %, activado tras +4 % neto. |
| B7_lento | Momentum 128 > 3 %, cuatro confirmaciones, TP 6 %, SL 4 %, espera 128 y mínimo 64 ticks para salir por señal. |

Las confirmaciones son observaciones consecutivas de la condición; el mínimo de permanencia bloquea la salida por señal, no las protecciones de riesgo.

## Paciente y Lento: generaciones 1 y 2

- **Paciente 1:** B6_paciente; exposición 50 %, momentum 32 > 2 % confirmado tres veces, SL 3 %, trailing 3 % activado desde +4 %, espera 64.
- **Paciente 2:** mantiene su gestión y añade a la entrada `SMA32 > SMA128` y `precio actual > SMA128`.
- **Lento 1:** B7_lento; exposición 50 %, momentum 128 > 3 % confirmado cuatro veces, TP 6 %, SL 4 %, espera 128.
- **Lento 2:** sustituye la entrada por momentum 16 > 1 % confirmado dos veces y el mismo filtro de tendencia; conserva el momentum 128 para las salidas y la gestión del padre.

Estos cambios no implementaron exposición dinámica, ventas parciales ni adaptación de umbrales a la volatilidad. No incluirlos en el informe como trabajo realizado.

## Resultados y motivo del descarte

En las cuatro series oficiales iniciales de la comparación generacional, Paciente 1 alcanzó $11.400,25 de patrimonio medio y Paciente 2 $11.389; la segunda redujo comisiones y mejoró el peor final de ese lote. Lento 2 no produjo una mejora consistente. En las ocho oficiales completas, las medias de Paciente 1 y 2 fueron $10.740,25 y $10.761,375: hubo mejoras puntuales, sin una ventaja amplia y estable.

La ampliación de cobertura fue decisiva:

| Subconjunto | Series | Paciente 1: patrimonio medio | Paciente 2: patrimonio medio |
|---|---:|---:|---:|
| Ocho oficiales actuales | 8 | $10.740,25 | $10.761,38 |
| Recreadas | 70 | $9.809,00 | $9.904,64 |
| Práctica inicial antigua, por separado | 1 | $4.619,00 | $6.518,00 |
| Conjunto completo realmente evaluado | 79 | $9.837,61 | $9.948,53 |

Sobre las 70 recreadas, las comisiones medias fueron $563,93 y $471,43; Paciente 1 superó la caja inicial en 32 de las 70 y Paciente 2 en 33. Los dos promedios quedaron por debajo de $10.000, incluso excluyendo la práctica antigua. Fuente: `05_pacientes_cobertura_completa/agregados.json`, grupos `recreada`, `catedra`, `original` y `global`.

El diseño es compatible con varias debilidades: entradas después de una subida, salidas ante retrocesos recuperables, rotación y comisiones, y exposición limitada durante movimientos favorables. Estas explicaciones no constituyen una atribución causal aislada de cada pérdida: no se realizó una ablación exhaustiva de todos esos factores.

Se decidió explorar otra lógica y se desarrolló la familia M: comprar en niveles normalizados bajos, sostener la posición y vender en niveles altos. Después de iterar sus bandas, el equipo seleccionó M105-225. M no fue simplemente Z con otros porcentajes: cambió la señal de entrada/salida, la acumulación y el presupuesto de exposición. Su mejor desempeño en los conjuntos evaluados no demuestra superioridad universal ni menor riesgo intrarronda.

## Límites que debe respetar el informe

- Separar el lote de cuatro oficiales, el de ocho oficiales y el ampliado de 79: sus promedios no son intercambiables.
- No llamar «78 series» al promedio global de este último informe de Z; sí se puede calcular un subconjunto de 78 excluyendo la práctica inicial, pero sería un agregado nuevo y debe identificarse como tal.
- Las tres reconstrucciones alineadas tempranas de Tesla, AMD y Apple son distintas de los 70 bloques recreados. Aparecen como entradas adicionales en las primeras etapas, no como nuevas series oficiales.
- Los parámetros se exploraron usando series conocidas; no presentar el proceso como validación ciega ni sus archivos como muestras estadísticamente independientes.
- Todo Z fue un prototipo Python. La equivalencia contable con el testbench no certifica implementación Assembly, recursos FPGA o deadlines de Z.
