# Contexto Z — antecedentes temporales para redactar el informe

**Carpeta temporal de contexto en `pre-entrega`.** Reúne los experimentos que quedaron localmente sobre la familia que hoy llamamos **Z** y que el código histórico denomina **Baltazar/Baltasar**. No es la implementación final del Proyecto 4: el equipo seleccionó **M105-225**, software optimizado e ISA original.

Todo lo publicado en esta actualización queda dentro de esta carpeta. Para retirarlo del árbol de la entrega basta eliminar `contexto Z/`; no se añadieron dependencias ni enlaces desde archivos operativos del proyecto hacia ella. No se modificaron Assembly, RTL, configuración, estrategia ni imagen FPGA, y no se volvieron a simular las estrategias para preparar este contexto.

## Qué leer primero

1. [Resumen para el otro chat](CONTEXTO_PARA_INFORME.md): origen, mecanismo, variantes y motivo del descarte.
2. [Parámetros de Paciente y Lento, generaciones 1 y 2](03_paciente_y_lento_generaciones/plan.json), junto con sus [reglas de entrada](03_paciente_y_lento_generaciones/tools/generations.py) y [gestión de posiciones](03_paciente_y_lento_generaciones/tools/baltazar.py).
3. [Comparación de las cinco alternativas en ocho series oficiales](04_ocho_oficiales/resumen.csv) y sus [agregados](04_ocho_oficiales/agregados.json).
4. [Evaluación ampliada de Paciente 1 y 2](05_pacientes_cobertura_completa/agregados.json). **Esta evaluación contiene 79 series: 70 recreadas + 8 oficiales actuales + 1 práctica inicial antigua.** Usar el grupo `recreada` para hablar exclusivamente de las 70, y `catedra` para las ocho actuales.

## Etapas conservadas

| Carpeta | Contenido |
|---|---|
| [01_origen](01_origen/) | Prototipos de momentum, límites de exposición y salidas TP/SL/trailing; comparación con D y con tres reconstrucciones alineadas de series conocidas. |
| [02_reduccion_comisiones](02_reduccion_comisiones/) | Esperas, confirmaciones de señales, salidas más amplias y combinación de cambios. Aquí aparecen las variantes Paciente y Lento. |
| [03_paciente_y_lento_generaciones](03_paciente_y_lento_generaciones/) | D, Paciente 1, Paciente 2, Lento 1 y Lento 2 sobre cuatro series oficiales. |
| [04_ocho_oficiales](04_ocho_oficiales/) | Las mismas cinco alternativas sobre las ocho series oficiales, con PDF y gráficos. |
| [05_pacientes_cobertura_completa](05_pacientes_cobertura_completa/) | Paciente 1 y 2 sobre 79 series únicas; incluye promedio global, grupos por origen/acción, PDF y trazas. |
| [datos](datos/) | Todas las entradas necesarias para interpretar los experimentos: ocho oficiales, práctica antigua, 70 recreadas comprimidas y tres reconstrucciones alineadas tempranas. |

Cada etapa conserva sus CSV de resumen, planes, código Python histórico, testbench contable, verificaciones guardadas y gráficos/informes existentes. Las trazas completas y los registros de operaciones están en `trazas_resultados.tar.gz` dentro de cada etapa. [Inventario de etapas](inventario_etapas.json).

## Informes existentes

- [PDF: cinco alternativas sobre ocho series oficiales](04_ocho_oficiales/informes/AC4_Comparacion_5_estrategias_8_series.pdf).
- [PDF: Paciente 1 frente a Paciente 2 sobre todas las entradas de aquella evaluación](05_pacientes_cobertura_completa/informes/AC4_Paciente_1_vs_2_todas_las_series.pdf). Se conserva el documento histórico de 87 páginas; su promedio global utiliza 79 entradas, no exclusivamente las 70 recreadas.

## Cómo interpretar los archivos

- **`Paciente_1`, `Paciente_2`, `Lento_1`, `Lento_2` son variantes de Z.** Las letras `B0` a `B7` de la segunda etapa son nombres históricos del código; no corresponden a las variantes A–E de reversión a la media de D.
- `resumen.csv` registra patrimonio, órdenes, comisiones, caja, inventario y caídas; `agregados.json` o `comparacion_agregada.json` separa los conjuntos evaluados.
- `plan.json` guarda las reglas y fuentes de la etapa; `conclusiones.json` conserva las observaciones realizadas entonces. Los nombres Baltazar y las rutas absolutas son parte del registro original, no una indicación de ejecutarlo desde esas rutas en otro equipo.
- [Mapa portátil de entradas](datos/mapa_entradas.json): para cada entrada y etapa indica el archivo relativo de esta carpeta o el miembro dentro del archivo de las 70 recreadas. Se contrastaron los SHA-256 de las entradas.
- Los scripts originales se conservan **sin reescribir sus rutas históricas**. Para ejecutar fuera de la Mac original hace falta adaptar las rutas de lectura/salida utilizando ese mapa. Para consultar el contexto o rehacer gráficos desde las trazas no hace falta volver a simular.
- Las verificaciones archivadas acreditan contabilidad en simulación; **Z nunca se implementó en Espino ni se validó en la FPGA**. No atribuirle los tiempos o pruebas físicas de D o M.

## Integridad y retirada

`SHA256SUMS` identifica todos los archivos publicados en este paquete. Desde esta carpeta se pueden verificar con `shasum -a 256 -c SHA256SUMS`. El inventario de contenido de los archivos comprimidos se conserva en `inventario_trazas.json`.

Se excluyeron cachés, ejecutables de simulación, compilaciones y archivos de macOS. Los resultados históricos y sus entradas se conservan; no se publicaron datos de USB ni respaldos de la flash. Esta carpeta se puede quitar en bloque antes de preparar la entrega evaluada; no se cambió `main`.
