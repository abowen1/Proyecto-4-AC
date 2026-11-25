# M105-225: carga en Go Board 17 y estado para el informe

**Actualización posterior del 25/11:** el equipo confirmó una prueba física exitosa con la maestra. [Nota de seguimiento](../M105_225_placa17_2026-11-25/README.md). El texto siguiente conserva el estado y las comprobaciones del 24/11.

24 de noviembre de 2026. **Se puede iniciar el informe con la estrategia y la implementación ya elegidas.** La imagen fue cargada y verificada en la placa; la comunicación física con la maestra y el reinicio de la cartera entre rondas siguen pendientes de prueba.

## Decisión definitiva de implementación

El equipo mantiene **M105-225 con software optimizado sobre la ISA original de Espino**, sin QCAP ni shifter en la imagen final. Mdip es solo su alias de conversación; el nombre oficial sigue siendo M105-225. No se cambió la estrategia, el assembly, RTL ni la configuración durante esta carga. Se utilizó el bitstream existente, sin regenerarlo.

Después de revisar las alternativas, Andrés consultó al profesor Jorge Gómez sobre hasta dónde optimizar. Según la respuesta que Andrés compartió, el profesor indicó que pueden justificar el punto de detención mediante la ley de Amdahl y el roofline vistos en clases. **La decisión de detener las optimizaciones es del equipo**: no implica que el profesor haya certificado esta imagen o preferido software frente a QCAP.

La justificación debe reconocer que QCAP mejora tanto el promedio como el máximo observado, aunque la mejora media adicional frente al software optimizado es de aproximadamente 0,02268 %. La versión elegida ya cumple el presupuesto temporal con margen; el informe debe argumentar ese punto de detención con las mediciones y Amdahl/roofline, sin presentar el ahorro de recursos como una obligación del enunciado ni afirmar que software sea la opción más rápida.

Las comparaciones, métricas, validaciones en simulación e imagen reproducible se conservan en el [reporte de optimización](../../estrategia/M105_225_optimizacion/README.md). La [elección financiera](../../estrategia/seleccion_M105_225_2026-11-24/README.md) documenta por qué se escogió esta variante por su desempeño medio en las 78 series.

## Identificación de la placa

**Go Board 17**: el número 17 está escrito con plumón en la placa asignada al equipo. Es una identificación humana, no un número de serie electrónico. Andrés confirmó que es la misma placa que anteriormente ejecutó D y se comunicó con la maestra en la práctica.

## Comprobaciones realizadas hoy

1. Se verificó que la imagen corresponde a M105-225 optimizado, ISA original: 32.220 bytes; SHA-256 `5be11e8803854d23bc61d15b504b2621084c08c01417fb07f629ad3abd841551`.
2. Antes de reemplazar D se leyeron dos veces los primeros 64 KiB de la flash: ambas lecturas fueron idénticas. El respaldo binario se conserva solo localmente; no se publica.
3. Se programó la flash: el programador terminó con código 0, **VERIFY OK y CDONE alto**.
4. Andrés desconectó y reconectó la alimentación USB e informó **00 en los displays**.
5. Después de esa reconexión se comparó la flash contra la imagen aprobada con `iceprog -c`, sin regrabar: código 0, **VERIFY OK y CDONE alto**. Se confirmó la persistencia de la imagen. El acceso del programador también reinicia la configuración; no verifica el estado de caja e inventario.

La consulta de identificación de la flash devolvió `FF FF FF FF`, como en registros previos. No se interpretó como identificación válida: se comprobó la lectura mediante dos respaldos idénticos y la escritura mediante verificación. Los registros completos y el [resultado estructurado](validacion.json) conservan esta advertencia.

## Qué se ha validado y qué falta

| Aspecto | Estado |
|---|---|
| Estrategia e implementación seleccionadas | M105-225, software optimizado, ISA original |
| Equivalencia Python/RTL e integración simulada | Completadas en las etapas anteriores; ver reporte técnico |
| Síntesis, recursos y timing de la imagen | Completados; objetivo de 25 MHz |
| Carga de esa imagen en la placa 17 | Verificada |
| Persistencia de la imagen tras cortar alimentación | Verificada por comparación de la flash |
| SPI físico de esta imagen con la maestra | Pendiente |
| Decisiones físicas y reinicio de caja/inventario entre rondas | Pendientes |

Hoy no se dispone de la maestra. **El antecedente de que D se comunicó correctamente no sustituye la prueba física de M105-225.** Se conserva el protocolo SPI, el formato de órdenes y los pines; eso está respaldado por las pruebas de integración simuladas, pero no se informa una ronda bursátil física completada hoy.

## Prueba pendiente con la maestra

La placa ya está programada: no hace falta recompilar ni volver a cargarla para conectarla a la maestra. Comprobar cableado SPI según los pines del proyecto, tierra común y condiciones eléctricas del curso; conectar con la alimentación desconectada y luego realizar una ronda de prueba.

Verificar recepción de precios, decisiones y cantidades frente a la referencia, operación al período que use la maestra y arranque de cada ronda con caja de 10.000 e inventario vacío. Para reiniciar la cartera se requiere cortar y restablecer la alimentación de la Go Board; **los botones no reinician la cartera**. Que la maestra reinicie su ronda no demuestra que la Go Board haya reiniciado su estado.

No se requieren nuevas optimizaciones para esta prueba. Si aparece una falla de integración real, se investigará antes de afirmar que la validación física está completa.

## Uso para el informe

Pueden redactarse la estrategia, su selección, arquitectura, equivalencia funcional, metodología de medición, comparación de alternativas, Amdahl, roofline, recursos/timing y justificación de detener la optimización. Para el apartado de ejecución física se debe citar lo comprobado aquí y **dejar pendiente la validación con la maestra y el reinicio de cartera** hasta disponer de evidencia.

Este registro está en `pre-entrega`, como evidencia de desarrollo y contexto para el equipo. No se ha preparado ni publicado todavía una entrega evaluada en `main`.
