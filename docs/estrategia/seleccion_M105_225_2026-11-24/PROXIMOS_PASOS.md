# Incorporación de M105-225: plan y criterios de aprobación

La elección bursátil quedó cerrada por el equipo el 24/11/2026. Este documento ordena el trabajo siguiente; **esta publicación no cambia assembly, RTL, imágenes ni la placa**. La referencia bursátil Python seleccionada es M105-225. El código operativo existente y los objetivos `test-final/build-final/program-final` siguen apuntando a D hasta que se adapte y apruebe la transición.

## 1. Congelar la referencia y el contrato de mercado

Conservar `decision.json`, `tools/m_bands.py`, los 78 archivos de entrada con sus hashes y los resultados por tick que se generan con `tools/reproducir.py`. Estos serán el oráculo de equivalencia. Fijar enteros, inicialización, presupuesto de entrada, orden previa, cantidades efectivamente ejecutadas, comisiones y estados. Preservar decisión en t y ejecución en t+1; no decidir usando precios futuros. La liquidación enclavada, el cierre de acumulación y la posibilidad de reentrada son parte del algoritmo, no detalles opcionales.

Criterio: referencia exacta reproducible con resultados seleccionados en las 78 series; archivo de configuración y revisión fijados. Los umbrales 105/225 y las reglas no se retocan durante una optimización de rendimiento.

## 2. Implementar una base funcional en Espino

Reutilizar la lectura SPI, las direcciones de periféricos, el ensamblador y la contabilidad de la orden previa que ya existen. Sustituir el algoritmo de D por la máquina de estados M, inicialmente en una implementación simple que sirva de control. La placa solo recibe precios; debe reconstruir internamente caja/inventario con el precio actual y la decisión previa, exactamente como la maestra. Usar las operaciones e instrucciones que soporte cada variante, sin asumir multiplicación o división de la ISA original.

Probar casos pequeños deliberados: precios104/105/106 y224/225/226, caja justo suficiente o insuficiente para comisión, compras/ventas de más de63 repartidas en varios ticks, salto de precio entre decisión y ejecución, salida de la banda de compra, liquidación que continúa bajo225, reentrada, posición abierta al terminar y reinicio de estado. Verificar prefijos causales y rangos de enteros/memoria.

Criterio: mismas decisiones byte por byte, llenados reales, caja, inventario, órdenes, comisiones y patrimonio que Python; no basta coincidir en el patrimonio final.

## 3. Integrar y aprobar simulación completa

Adaptar el banco de equivalencia de D para M y conservar los bancos originales. Repetir las pruebas del ensamblador, instrucciones y SPI. Validar las 78 series completas con referencia M donde el banco permita acelerar el tiempo ocioso; además correr la temporización real en las tres velocidades del curso y el testbench oficial sin alterar sus reglas.

Verificar arranque, una respuesta por precio, consumo de NEW_PRICE, MISO sin valores desconocidos, desfase de una transacción, plazos de respuesta, contabilidad y reinicio entre rondas. Un ensayo rápido de 2000 ticks no sustituye los resultados financieros de 20000 ni viceversa. Los bancos deben documentar cómo se inicializa y termina cada ronda.

Criterio: regresiones aprobadas, equivalencia por tick y ninguna respuesta fuera de plazo en los casos de temporización probados. Los ensayos sobre Python y la contabilidad Verilog previos no son aprobación automática del nuevo assembly.

## 4. Medir antes de optimizar

Perfilar M en su base funcional: instrucciones ejecutadas, ciclos medios y máximos por precio, caminos de compra/venta/mantener y margen del plazo. M ya no calcula SMA32; el perfil y los porcentajes de Amdahl de D no describen su nuevo costo. Cantidades, división por precio y contabilidad pueden dominar, pero hay que medirlo.

Evaluar las alternativas software/hardware existentes, incluido shifter y QCAP, sobre el mismo M si son pertinentes. Conservar los cambios que ayuden a cumplir plazos o aporten una mejora defendible para las alternativas exigidas por el proyecto. No agregar hardware por intuición ni optimizar la rentabilidad cambiando el algoritmo durante esta comparación. Si una alternativa previa no ayuda a M, registrar ese resultado y escoger una alternativa justificada por su perfil.

Criterio: mismas decisiones y resultados que la base tras cada cambio, ciclos y recursos medidos, comparación de las alternativas de hardware exigidas y justificación por evidencia. La menor latencia no se debe conseguir modificando comisiones o reglas de la maestra.

## 5. Generar y comprobar las imágenes de placa

Sintetizar y hacer place-and-route a 25 MHz para cada candidata de hardware que deba compararse. Revisar que código y datos quepan, recursos de la FPGA, memoria y cierre de timing. Fijar cuál imagen se elige, sus fuentes y hashes. Volver a ejecutar las regresiones con la imagen/programa que realmente se compilará; adaptar los objetivos de compilación/prueba para que no sigan ensamblando D por accidente.

Criterio: timing aprobado y capacidad suficiente en la Go Board, imagen identificable y pruebas de integración correspondientes aprobadas. La estrategia elegida no determina por sí sola cuál variante de hardware gana.

## 6. Validación física y cierre

Conectar la Go Board cuando haya una imagen preparada y comprobada. Programarla, verificar la flash y comprobar que arranca también tras cortar y volver a dar alimentación. Enviar una secuencia conocida con una maestra compatible, observar respuestas y compararlas con las esperadas; repetir con la FPGA maestra del curso y las velocidades de competencia cuando esté disponible. Verificar pines/conexión, sincronización y estado inicial de cada ronda. Confirmar el mecanismo de reinicio: actualmente el código bursátil no reinicia caja/inventario con los botones.

La carga VERIFY OK y un diagnóstico de botones/LED prueban programación o funciones aisladas; la aprobación bursátil requiere recepción de precios y decisiones correctas. Registrar traza o evidencia de la ronda física y el procedimiento de reinicio. Conservar el informe financiero de78 series separado de la evidencia de ejecución real.

Criterio: comunicación y resultados físicos reproducibles, procedimiento de conexión/reinicio documentado, imagen final fijada y pruebas completas archivadas. Después preparar `main` con los archivos de entrega, informe del algoritmo, alternativas de hardware, mediciones y limitaciones; `pre-entrega` conserva la exploración. No publicar una prueba física como aprobada antes de realizarla.
