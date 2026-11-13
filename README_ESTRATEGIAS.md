# AC4 — Traspaso de estrategias y resultados para Coni y su Work

La comparación posterior de hardware conserva exactamente D: [dos alternativas, mediciones y pruebas de placa](docs/informe/03_hardware_2026-11-12/README.md). Se recomienda el desplazador acotado: 28,16 % menos ciclos promedio que el software optimizado. Las alternativas de hardware A/B no son las estrategias bursátiles A/B históricas.

**Decisión final del equipo, 12 de noviembre de 2026: D original, SMA32 y banda 1, sin subvariaciones y sin techo de retiro en 20.000 ni 30.000.** Los experimentos de salida permanente quedan como historia y no forman parte de la estrategia elegida. D se implementó en `sw/trade.s`; ver [reglas y evidencia de implementación](docs/estrategia/D_implementacion.md).

El contenido original del 11 de noviembre y las recomendaciones provisionales posteriores se conservan como historia del proceso; la elección actual del equipo es D, no A.

Repositorio del grupo: <https://github.com/abowen1/Proyecto-4-AC>.

Zona compartida de trabajo: [rama pre-entrega](https://github.com/abowen1/Proyecto-4-AC/tree/pre-entrega). Preparar allí avances y propuestas; `main` queda reservada para seleccionar el material de entrega. Separar ramas organiza el trabajo, no oculta información a personas con acceso al repositorio.

Este documento es autocontenido: reúne las reglas del simulador, las estrategias exactas, sus parámetros, los resultados y los límites de lo comprobado. Permite reconstruir las variantes y preparar la parte del informe correspondiente al algoritmo y sus pruebas. **El cuerpo original describe las referencias Python; la implementación posterior de D y sus métricas tienen evidencia separada en el enlace anterior. Las demás variantes no están implementadas en Espino.**

El objetivo de las comparaciones originales era encontrar una candidata que funcionara en las series desconocidas de la presentación. Obtener el máximo patrimonio en la práctica conocida es solo una observación inicial. No queremos una estrategia que memorice precios, ticks o tramos de este archivo.

Las rutas de código y evidencia mencionadas son relativas a la raíz de la rama `pre-entrega`, que reúne la base, pruebas y resultados. Si solo recibes una copia de este documento, las especificaciones siguientes son la referencia para reconstruir el experimento.

## 1. Qué se hizo y qué falta

Se realizaron tres lotes, siempre con la misma serie de práctica:

1. Cinco referencias: mantener, medias móviles, momentum, regresión lineal incremental y reversión a la media.
2. Cinco versiones de reversión: A, B, C, D y E.
3. Ocho versiones: A y D originales, más AP/DP con pánico, AF/DF con filtro de tendencia y AE/DE con objetivo de exposición.

Son **18 ejecuciones registradas y 15 configuraciones distintas**: la reversión inicial es A, A se repite en los tres lotes y D en los dos últimos.

Está comprobado:

- Simulación causal en Python, con ejecución de la orden al precio siguiente, comisión, restricciones de caja e inventario y marcado del patrimonio a mercado.
- Reversión A y D de los lotes posteriores coinciden por tick con sus resultados anteriores.
- Contabilidad contrastada con la tarea original de SystemVerilog del testbench de Canvas, por tick y para cada variante de los lotes de validación.
- 22 pruebas automatizadas aprobadas en la revisión más reciente, incluyendo ensamblador, causalidad, regresión incremental y protecciones.

Sigue pendiente:

- Validación en otras series y elección de estrategia por el equipo.
- Assembly de las estrategias activas. `trade.s` todavía solo recibe precios y responde mantener.
- Equivalencia de decisiones entre la futura referencia elegida y assembly, durante toda la serie.
- IC, ciclos, CPI, tiempo por tick y cumplimiento de los plazos de las estrategias activas.
- Dos alternativas de hardware, LUTs, BRAM, frecuencia máxima, speedup, Amdahl y roofline.
- Validación física del conjunto en Go Board y con la FPGA maestra.

No hay una fecha final de entrega confirmada en este documento. La transcripción de clase contiene discusión de fechas y de inicio de rondas, sin un acuerdo inequívoco; no convertir ejemplos de esa discusión en reglas nuevas.

## 2. Mercado y protocolo que debe reproducir cualquier referencia

### 2.1. Parámetros usados

| Concepto | Valor del experimento |
|---|---:|
| Caja inicial por simulación | 10.000 |
| Inventario inicial | 0 acciones |
| Comisión fija por orden ejecutada | 5 |
| Precio recibido | Entero de 1 a 255 |
| Cantidad de una orden | Entero de 0 a 63 |
| Precios en la práctica completa | 20.000 |
| Longitud predeterminada del testbench Canvas | 2.000 |

Caja y comisión se leen de las constantes `CAJA0` y `COMISION` del testbench. Hay que revisar cualquier actualización oficial antes de la entrega. Son reglas del experimento, no parámetros que podamos modificar para favorecer una estrategia.

La serie completa tiene ticks 0 a 19.999, primer precio 151, último 98 y precios observados entre 72 y 190. Estos datos describen el archivo probado; **no deben incorporarse como conocimiento del futuro en el algoritmo**.

SHA-256 de la serie utilizada:

```text
9db90594ce790c7d046f4045a0affcefdb04012a7f2e2ab989ba45d15794ec7f
```

### 2.2. Orden temporal: lo más importante

En cada tick `n` sucede esto:

1. Llega el precio `p[n]`.
2. Se ejecuta al precio `p[n]` el byte preparado en el tick anterior.
3. Se actualizan caja, inventario y patrimonio con esa ejecución.
4. El algoritmo incorpora `p[n]`, calcula su señal y prepara la orden del tick siguiente.

La decisión inicial es mantener. La decisión calculada después del último precio **no se ejecuta**, porque ya no existe un precio siguiente en esa simulación.

Ejemplo: observar 100 y preparar comprar 3 no permite comprar a 100. Si el precio siguiente es 110, la compra se intenta a 110, con su comisión y con el recorte de cantidad que corresponda.

El testbench y el protocolo real pueden repetir la última decisión si el procesador no escribe otra a tiempo. Las referencias Python actuales **suponen que cada decisión llega a tiempo**: no simulan esos atrasos.

### 2.3. Byte de decisión

```text
bits [7:6] = acción: 00 mantener, 01 comprar, 10 vender, 11 reservado/mantener
bits [5:0] = cantidad q: 0 a 63

mantener: 0x00
comprar:  0x40 | q
vender:   0x80 | q
```

Una cantidad cero no ejecuta una operación ni paga comisión. Tampoco se cobra comisión por una compra imposible o una venta que no pueda ejecutarse.

**63 es el máximo por orden, no el máximo de acciones acumuladas.** Una señal persistente puede producir varias compras consecutivas y acumular más de 63 acciones; una venta total puede necesitar varios ticks.

### 2.4. Contabilidad exacta

Sean `caja`, `acciones`, `p` el precio de ejecución y `C=5` la comisión:

```text
COMPRA:
    q_ejecutada = min(q_pedida, max(0, floor((caja - C) / p)))
    si q_ejecutada > 0:
        caja     -= q_ejecutada * p + C
        acciones += q_ejecutada
        órdenes  += 1

VENTA:
    q_ejecutada = min(q_pedida, acciones)
    si q_ejecutada > 0 y caja + q_ejecutada * p >= C:
        caja     += q_ejecutada * p - C
        acciones -= q_ejecutada
        órdenes  += 1

PATRIMONIO:
    W = caja + acciones * p
    peak = max(peak, W)             # peak inicia en 10.000
    max_drawdown = max(max_drawdown, peak - W)
```

No hay deuda ni ventas en corto. La maestra lleva la contabilidad oficial; la estrategia puede mantener una copia usando su orden anterior y el precio recibido, sin consultar patrimonio a la maestra. Esa copia solo coincide si replica correctamente las órdenes ejecutadas y su sincronización.

Las acciones remanentes se valoran al último precio. **No se obliga a liquidar al terminar**, no se cobra una comisión ficticia de cierre y no se interpreta patrimonio como efectivo disponible.

### 2.5. Cantidades comunes de las variantes sin límite de exposición

Una señal positiva pide:

```text
q = min(63, max(0, floor((caja_actual - C) / precio_actual)))
```

Una señal negativa pide `min(63, acciones_actuales)`. Una señal neutral o una cantidad cero produce mantener.

El cálculo de cantidad usa el precio que ya conocemos. La maestra recorta otra vez la orden con el precio real del siguiente tick, que todavía desconocemos al decidir. En una subida puede comprar menos de lo pedido; en una bajada no aumenta automáticamente la cantidad que habíamos pedido.

No existe un tope adicional de inversión para A/B/C/D/E, AP/DP o AF/DF. Las señales de compra pueden acabar utilizando casi toda la caja.

## 3. Definiciones comunes de señales

Una señal vale `+1` comprar, `−1` vender o `0` neutral. **Neutral conserva la posición existente; no significa vender y quedar en efectivo.**

Un promedio móvil de ventana `N`, `SMA_N`, contiene los últimos `N` precios, **incluido el que acaba de llegar**. Se espera a llenar la ventana antes de operar. Con `N=32`, el primer tick que puede tener señal es el 31.

Las bandas están expresadas en unidades del precio normalizado, no en porcentajes ni dólares de patrimonio. Los umbrales son estrictos: si la diferencia es exactamente igual a la banda, la señal es neutral.

Las referencias usan enteros y comparaciones por productos cruzados para evitar divisiones y redondeos del promedio. Esto hace el resultado determinista y define el comportamiento que deberá reproducir el assembly.

## 4. Primer lote: las cinco familias del enunciado

El enunciado menciona familias, no algoritmos completos con parámetros obligatorios. Estas fueron nuestras decisiones iniciales de implementación.

### 4.1. Mantener sin operar

Siempre escribe `0x00`, sin parámetros ni órdenes. Es la referencia de no operar: termina con 10.000, sin comisión ni drawdown.

Es distinta de mantener una posición comprada previamente y distinta del benchmark comprar y mantener.

### 4.2. Cruce de medias móviles

Parámetros: ventana corta 8, larga 32, banda 1.

```text
si SMA8 - SMA32 >  1: comprar
si SMA8 - SMA32 < -1: vender
en otro caso: mantener
```

Comparación entera exacta: `d = suma_8 * 32 - suma_32 * 8`; comparar `d` con `±256`. La idea es seguir la tendencia reciente cuando el promedio corto se separa del largo.

### 4.3. Momentum

Parámetros: retardo de 8 ticks, banda 2.

```text
d = precio_actual - precio_de_hace_8_ticks
si d >  2: comprar
si d < -2: vender
en otro caso: mantener
```

Se requieren 9 precios para comparar el actual con el de 8 ticks antes. No usa promedio ni predicción adicional. Su idea es que el movimiento reciente continúe.

### 4.4. Regresión lineal incremental

Parámetros: ventana 16, predicción de un tick, banda 1.

Se ajusta `y = a*x + b` a los últimos 16 precios, usando `x=0..15`; se predice el valor de `y` en `x=16`. Compra si el predicho supera al precio actual por más de 1, vende si está por debajo por más de 1 y mantiene en el resto.

Definiciones:

```text
N = 16
Sy  = suma de precios de la ventana
Sxy = suma de x * precio[x], con el más antiguo en x=0
Sx  = 120
Sxx = 1240
D   = N*Sxx - Sx*Sx = 5440
A   = N*Sxy - Sx*Sy

numerador_diferencia = Sy*D + A*(N*N - Sx) - precio_actual*N*D
umbral = N*D = 87040

si numerador_diferencia >  umbral: comprar
si numerador_diferencia < -umbral: vender
en otro caso: mantener
```

Con la ventana llena, al retirar `old` y agregar `new`:

```text
Sxy_nueva = Sxy_anterior - (Sy_anterior - old) + 15*new
Sy_nueva  = Sy_anterior - old + new
```

Durante el llenado se agrega cada nuevo precio con su índice actual. No hay redondeo de una predicción decimal: se compara directamente su numerador. Las pruebas contrastan el estado incremental con el cálculo completo de cada ventana.

### 4.5. Reversión a la media inicial, luego llamada A

Parámetros: ventana 32, banda 2.

```text
si SMA32 - precio_actual >  2: comprar
si SMA32 - precio_actual < -2: vender
en otro caso: mantener
```

La hipótesis es que una separación del promedio reciente puede ser temporal. No detecta por sí sola una tendencia bajista sostenida. El promedio también puede bajar: no espera necesariamente recuperar el precio al que compró y puede vender con pérdida.

Comparación entera exacta para ventana `N` y banda `B`:

```text
d = suma_N - N*precio_actual
si d >  B*N: comprar
si d < -B*N: vender
en otro caso: mantener
```

### 4.6. Resultados del primer lote: serie completa

Capital inicial 10.000; las comisiones ya están descontadas del patrimonio.

| Estrategia | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Drawdown máximo |
|---|---:|---:|---:|---:|---:|
| Mantener sin operar | 10.000 | 0 | 0 | 0 | 0 |
| Medias móviles | 3.817 | −6.183 | 474 | 2.370 | 8.260 |
| Momentum | 2.048 | −7.952 | 597 | 2.985 | 9.526 |
| Regresión lineal incremental | 90 | −9.910 | 1.264 | 6.320 | 10.495 |
| Reversión inicial / A | 18.502 | +8.502 | 729 | 3.645 | 5.630 |

Estos resultados descartan esas configuraciones concretas como ganadoras de esta comparación; no prueban que toda estrategia de momentum o regresión sea inferior a toda estrategia de reversión.

## 5. Segundo lote: reversión A, B, C, D y E

Se cambiaron ventana o banda, una variable por vez respecto de A. Se mantuvieron contabilidad, señal neutral, cantidades y ejecución al siguiente precio.

| Variante | Ventana | Banda | Cambio respecto de A | Patrimonio final | Órdenes | Comisiones | Drawdown máximo |
|---|---:|---:|---|---:|---:|---:|---:|
| A | 32 | 2 | Ninguno; referencia original | 18.502 | 729 | 3.645 | 5.630 |
| B | 16 | 2 | Promedio más corto | 13.983 | 676 | 3.380 | 5.375 |
| C | 64 | 2 | Promedio más largo | 14.193 | 524 | 2.620 | 6.629 |
| D | 32 | 1 | Banda más estrecha | 17.909 | 1.415 | 7.075 | 7.017 |
| E | 32 | 4 | Banda más amplia | 8.559 | 148 | 740 | 6.123 |

A tuvo el mayor patrimonio final del lote. D se acercó, pero operó casi el doble y tuvo una caída absoluta máxima mayor. E redujo mucho la actividad, aunque eso no bastó para mejorar su patrimonio o evitar una caída importante.

No se hizo una búsqueda exhaustiva de ventanas y bandas. Después de observar este lote ya existe selección informada por la serie; no presentar una futura búsqueda sobre ella como validación independiente.

## 6. Tercer lote: protecciones de A y D

Árbol de variantes:

```text
Reversión
├── A: ventana 32, banda 2
│   ├── AP: A + pánico
│   ├── AF: A + filtro de tendencia
│   └── AE: A + objetivo de exposición
├── B: ventana 16, banda 2
├── C: ventana 64, banda 2
├── D: ventana 32, banda 1
│   ├── DP: D + pánico
│   ├── DF: D + filtro de tendencia
│   └── DE: D + objetivo de exposición
└── E: ventana 32, banda 4
```

**E y AE/DE no significan lo mismo:** E sola es la reversión con banda 4; el sufijo E en AE/DE identifica el límite de exposición. No se probaron combinaciones PF, PE, FE ni PFE.

### 6.1. AP y DP: salida por pánico

Parámetros adicionales: caída del precio de al menos 10% desde su máximo observado mientras haya inventario; espera de 32 ticks después de liquidar.

Estado adicional: `max_precio_posicion`, indicador `panico` y contador `espera`.

Reglas exactas, después de ejecutar la orden anterior al precio actual:

1. La señal base se actualiza siempre, incluso durante una liquidación o espera.
2. Si hay acciones, actualizar `max_precio_posicion = max(max_precio_posicion, precio_actual)`.
3. Si todavía no hay pánico y `100*precio_actual <= 90*max_precio_posicion`, activar pánico. La igualdad SÍ lo activa.
4. Mientras el pánico esté activo y haya acciones, pedir vender `min(63, acciones)` cada tick, ignorando las señales de compra y sin cancelar la salida si el precio rebota.
5. Al quedar sin acciones después de una liquidación de pánico, reiniciar el máximo, desactivar pánico, cargar `espera=32` y emitir mantener en ese tick.
6. En los 32 ticks siguientes, decrementar la espera y mantener. Recién en el siguiente tick se vuelve a permitir la señal base.
7. Si una venta normal deja el inventario en cero sin pánico activo, reiniciar el máximo pero no iniciar esa espera especial.

El máximo se refiere al PRECIO mientras existe inventario, no al máximo de patrimonio de la ronda ni al costo medio de compra. Si se sigue teniendo inventario entre ventas parciales y nuevas compras, se conserva ese máximo. El precio usado para empezar a observar una nueva posición es el del tick en que se ejecutó su primera compra.

Una posición de más de 63 acciones no puede liquidarse en una sola orden. Además, la venta se ejecuta al precio siguiente: el umbral del 10% **no garantiza limitar la pérdida al 10%**.

Esta variante prueba un paquete de salida y pausa; su efecto no permite atribuir por separado el resultado a la venta o a la espera. No se buscaron el mejor porcentaje ni la mejor espera.

### 6.2. AF y DF: filtro de tendencia

Parámetros adicionales: SMA corta 8 y SMA larga 32.

```text
si señal_base == comprar y SMA8 < SMA32:
    mantener
en otro caso:
    usar señal y cantidades de la base
```

La desigualdad es estricta: con promedios iguales no se bloquea la compra. En enteros, bloquear cuando `suma_8*32 < suma_32*8`.

No vende automáticamente al detectar tendencia bajista. Las ventas siguen la regla de reversión original. **Bloquear compras nuevas no elimina la exposición que ya existe.** Tampoco elimina una compra que ya estaba pendiente y se ejecutó antes de calcular el filtro del tick actual.

### 6.3. AE y DE: objetivo de exposición del 50%

No es solo reducir a la mitad cada compra. Se mantiene un objetivo de inventario calculado con el patrimonio y precio actuales, reservando una comisión:

```text
acciones_objetivo = max(0, floor((W_actual - C)/(2*precio_actual)))

si acciones_actuales > acciones_objetivo:
    vender min(63, acciones_actuales - acciones_objetivo)
si no hay exceso y señal_base == comprar:
    q_base = cantidad de compra de la estrategia original
    q = min(q_base, max(0, acciones_objetivo - acciones_actuales))
    comprar q si q > 0; de lo contrario mantener
si no hay exceso y señal_base == vender:
    vender con la cantidad original
en otro caso:
    mantener
```

La corrección de exceso tiene prioridad sobre la señal base, incluso si esta es neutral o comprar. Por lo tanto, una subida que aumente la proporción invertida puede causar una venta pequeña y pagar comisión. No hay banda de tolerancia alrededor del 50% en esta implementación.

El objetivo usa el precio conocido; una variación al ejecutar en el siguiente tick puede desplazar nuevamente la proporción. El máximo de 63 por orden también puede impedir una corrección instantánea. No afirmar que la exposición real nunca supera el 50%.

### 6.4. Resultados del tercer lote

| Variante | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Drawdown máximo |
|---|---:|---:|---:|---:|---:|
| A | 18.502 | +8.502 | 729 | 3.645 | 5.630 |
| D | 17.909 | +7.909 | 1.415 | 7.075 | 7.017 |
| AP | 10.939 | +939 | 592 | 2.960 | 5.275 |
| DP | 8.887 | −1.113 | 1.175 | 5.875 | 5.539 |
| AF | 10.002 | +2 | 106 | 530 | 3.186 |
| DF | 16.159 | +6.159 | 525 | 2.625 | 5.167 |
| AE | 9.612 | −388 | 922 | 4.610 | 3.141 |
| DE | 7.786 | −2.214 | 1.544 | 7.720 | 3.517 |

Interpretación sustentada por este lote:

- Ninguna protección superó a A en patrimonio final sobre esta práctica.
- DF fue la protección con mayor patrimonio final y redujo la caída máxima respecto de D.
- AE/DE redujeron la caída absoluta máxima, pero las correcciones también generaron operaciones y comisiones; terminaron por debajo del capital inicial.
- AF terminó casi igual que no operar, pero su drawdown fue 3.186: no tuvo la misma trayectoria ni el mismo riesgo que mantener sin operar.
- Pánico no fue una protección gratuita: puede vender durante una caída y perder parte del rebote posterior. Ese mecanismo es una explicación posible, no una atribución causal completa de todos los resultados.

## 7. Métricas y comparaciones que se deben explicar correctamente

### 7.1. Patrimonio y drawdown

Ganancia/pérdida es `W_final - 10.000`. Las comisiones de las tablas ya están incluidas; no volver a restarlas. El drawdown informado es el mayor valor de `peak_hasta_n - W_n`, en unidades monetarias del ejercicio. No es un porcentaje ni la caída desde el capital inicial.

Una estrategia puede tener drawdown mayor que 10.000 si primero ganó y luego perdió desde ese máximo. También puede sufrir una caída mayor que otra y seguir con más patrimonio, porque partía desde un máximo más alto.

No comparar automáticamente drawdown absoluto entre variantes con tamaños de patrimonio diferentes como si fuera una medida normalizada de riesgo. Para nuevas evaluaciones conviene agregar drawdown porcentual, definido y calculado por separado, sin sustituir silenciosamente las cifras originales.

### 7.2. Benchmark comprar y mantener

Se reproduce la fórmula del testbench:

```text
q_ref = floor((10.000 - 5)/primer_precio)
W_ref = 10.000 - 5 - q_ref*primer_precio + q_ref*ultimo_precio
```

En la serie completa: `q_ref=66`, caja residual 29, patrimonio final **6.497**. En los primeros 2.000 precios: **6.695**.

Esta referencia ideal compra al primer precio y no aplica a esa compra el límite de 63 por orden ni el desfase SPI. Es el benchmark oficial, **no una sexta estrategia que ya hayamos implementado en Espino**. Si se crea una estrategia ejecutable de comprar y mantener, debe identificarse como otra variante con sus restricciones reales.

### 7.3. Primeros 2.000 precios: resultado auxiliar

También se comparó el primer lote con la longitud predeterminada de Canvas:

| Estrategia | Patrimonio final | Órdenes | Comisiones | Drawdown máximo |
|---|---:|---:|---:|---:|
| Mantener | 10.000 | 0 | 0 | 0 |
| Medias móviles | 6.452 | 79 | 395 | 5.296 |
| Momentum | 7.722 | 105 | 525 | 3.755 |
| Regresión | 6.400 | 206 | 1.030 | 4.248 |
| Reversión A | 10.529 | 99 | 495 | 1.968 |

Se reinició caja y estado para cada ejecución. Este prefijo pertenece a la misma práctica: **no es una prueba independiente ni debe confundirse con la evaluación completa**. No hay un lote registrado de todas las protecciones a 2.000 precios.

## 8. Por qué no repetir sin cambios y cómo buscar una mejor candidata

Las estrategias son deterministas. Mismos precios, parámetros, orden de operaciones y código producen las mismas decisiones y resultados. Repetir sirve para comprobar reproducibilidad, no para estimar variación estadística.

La práctica completa ya fue examinada y utilizada para comparar variantes. Una división nueva de ese mismo archivo no borra lo aprendido sobre él. Los siguientes pasos son **propuestas de evaluación, todavía no ejecutadas**:

1. Mantener A y D como controles fijos y conservar también mantener y comprar y mantener como referencias.
2. Crear un conjunto de nuevas series para desarrollo y otro reservado para validación final, con identificadores y semillas registradas cuando corresponda. Separar primero, antes de ajustar parámetros.
3. Incluir escenarios laterales, alcistas, bajistas sostenidos, caídas bruscas, recuperaciones rápidas y niveles distintos de volatilidad. Respetar precios enteros 1–255 y documentar cómo se generan o normalizan. Las series sintéticas son escenarios controlados, no una garantía de realismo financiero.
4. No filtrar información futura al algoritmo: no usar media global, mínimo/máximo futuro ni normalización calculada con el resto de una serie como entrada online.
5. Explorar una cantidad acotada y documentada de configuraciones. Registrar todas las probadas, incluso malas. No elegir solo el mejor resultado de una búsqueda grande y presentarlo como evidencia independiente.
6. Variar inicialmente un mecanismo por vez. Si se combinan P/F/E, identificarlas como variantes nuevas, no como resultados ya existentes. Separar salida de pánico y espera ayuda a entender qué aporta cada una.
7. Medir patrimonio final, ganancia, órdenes, comisiones, drawdown absoluto y porcentual por serie; luego resumir mediana, peor caso y consistencia frente a referencias. No depender exclusivamente del promedio o de la serie que más favorece una variante.
8. Probar sensibilidad a parámetros vecinos. Un único valor extraordinario rodeado de resultados malos puede indicar fragilidad. No hacer que los parámetros dependan del número de tick o de reconocer el archivo de práctica.
9. Reservar evaluación final sin reajustes posteriores. Si se vuelve a ajustar después de verla, esa serie deja de ser una validación final limpia.
10. Asegurar que el algoritmo completo pueda funcionar de forma incremental, con memoria y aritmética acotadas, y después medirlo en Espino.

La evaluación fuera de placa puede explorar escenarios adicionales; el diseño de competencia no debe almacenar esas series ni usar información externa a los precios recibidos por SPI. Cualquier fuente externa de evaluación debe usarse conforme a las reglas que confirme el curso.

Posibles hipótesis para experimentar, sin resultados demostrados todavía: exposición con banda de tolerancia para evitar ventas diminutas, tamaños de orden menos agresivos, filtros de tendencia con umbral, pausas de pánico distintas o bandas relativas a volatilidad calculada solo con el pasado. Cada cambio necesita especificación, pruebas y una evaluación de costo para Espino.

## 9. Relación con Verilog y la evaluación de arquitectura

No basta con que una referencia gane en Python. La secuencia es: escoger candidatas, especificarlas exactamente, llevar una a assembly, medir dónde consume tiempo y elegir mejoras de hardware justificadas por esas mediciones. Si el costo resulta excesivo, se puede revisar también el algoritmo: es un proceso de co-diseño.

Los períodos de ronda indicados son 10 ms, 1 ms y 0,1 ms. A 25 MHz corresponden a 250.000, 25.000 y 2.500 ciclos brutos. El ejemplo SPI dura 9.500 ns y deja un presupuesto conservador de **249.762, 24.762 y 2.262 ciclos**, respectivamente, usando división entera. Hay que considerar sincronización y margen; estos números no certifican un plazo real cumplido.

Si dos implementaciones emiten los mismos bytes a tiempo, sus patrimonios serán iguales en la misma serie. La mayor velocidad puede evitar decisiones atrasadas o permitir más cálculo; no genera rentabilidad por sí misma.

La pauta revisada distribuye 6 puntos evaluados: algoritmo 1,0; assembly y mediciones 0,8; co-diseño 1,2; competencia 2,0; defensa 1,0. Exige al menos dos alternativas de hardware comparadas con software, manteniendo Espino dentro del ciclo de decisión. Confirmar cualquier actualización oficial.

### 9.1. Restricciones del core y representación

- Espino es RV32E: registros x0 a x15. No asumir un RISC-V completo.
- En la base, shifts están deshabilitados; el ensamblador propio los rechaza. No usar desplazamientos pensando que ya funcionan.
- Tampoco hay multiplicación/división disponibles en la versión inicial como instrucciones operativas para estas referencias.
- Los productos y divisiones que Python resuelve directamente pueden requerir rutinas o aceleradores. Python usa enteros sin límite práctico; en hardware hay que justificar anchos, signos, límites y overflow.
- Ventanas 16/32/64 facilitan ciertos diseños, pero dividir por potencias de dos mediante shift solo es una opción si ese hardware está implementado o se usa una equivalencia válida.
- Las comparaciones por productos cruzados conservan el resultado exacto y evitan redondear promedios, aunque sus productos también tienen costo.
- El cálculo de cantidad base y del objetivo de exposición contiene divisiones dependientes del precio. Puede ser un candidato a medir, pero **no está demostrado que sea el cuello de botella**.

Estado mínimo conceptual por variante: caja, acciones y orden pendiente; historial circular de precios; suma móvil y punteros; estado de la señal. Regresión añade suma ponderada. Pánico añade máximo, bandera y espera. Filtro añade la suma corta. Exposición necesita patrimonio y objetivo de acciones. El código Python conserva algunos estados auxiliares que se pueden simplificar sin cambiar decisiones; hay que demostrar equivalencia.

### 9.2. Base de hardware preparada

Se partió del Pochoco original, commit `33e8b5ae78faad7a9a36431d5ee8cf145e8573ec`, conservando sus 13 archivos RTL y pines sin cambios. No se incorporó el divisor por ocho de P2 ni las adaptaciones ASIC de P3. El reloj de simulación es directo a 25 MHz.

Se rescató el ensamblador de P2 y se prepararon:

- `trade.s`: 8 instrucciones estáticas, recibe precio y escribe mantener.
- `spi_diagnostic.s`: 9 instrucciones estáticas, devuelve `precio & 63` con acción mantener para probar una salida SPI variable.
- Pruebas de protocolo con 12 precios, incluidos extremos 1 y 255, ambos programas y los tres períodos de ronda.
- Testbench original de Canvas con mantener, 2.000 precios y ronda rápida: 4/4 chequeos aprobados.

Latencias máximas observadas en esas pruebas: mantener 18 ciclos / 720 ns; diagnóstico 20 ciclos / 800 ns. **No corresponden a A, D ni sus protecciones.** Las mediciones de instrucciones de esa base usan commits observados en una ventana desde recepción hasta escritura; no son todavía el CPI aislado del futuro kernel bursátil.

Actualización posterior del 11 de noviembre: se reparó la instalación reinstalando Yosys (ahora 0.70+post). Se generaron las imágenes de mantener y del ejemplo original de botones/LED: 1.082/1.280 celdas lógicas, 911 LUT4 y 12/16 BRAM; cierre de timing a 25 MHz, con Fmax estimada 44,81 MHz. No se cambió el reloj ni el RTL. Se cargó botones/LED con `VERIFY OK`; el usuario confirmó los cuatro botones y su funcionamiento después de desconectar/reconectar alimentación. Esto comprueba el arranque de esa base a 25 MHz; **no valida SPI físico ni la estrategia final**, cuyas métricas siguen pendientes. Detalles en `docs/evidencias/validacion_placa_2026-11-11.md`.

## 10. Qué verifican las pruebas y qué no

La última suite de 22 pruebas incluye codificación y validación del ensamblador; desfase de ejecución y última orden no ejecutada; caja, comisión e inventario; reservado y cantidad cero; marcado a mercado; causalidad por prefijos; regresión incremental frente a recálculo completo; parámetros y señales de reversión; liquidación de pánico por bloques y espera; filtro que bloquea compras pero no ventas; límite de exposición y corrección tras cambio de precio; causalidad de protecciones.

`verify_market.py` copia literalmente la tarea `ejecutar` y el estado contable del archivo oficial, los compila con Icarus y reproduce las decisiones de Python. Compara caja, acciones, patrimonio, órdenes y drawdown después de cada tick. Los lotes registrados verificaron:

| Lote | Ticks comparados con contabilidad Canvas |
|---|---:|
| Cinco familias completas + casos límite | 100.020 |
| Reversión A/B/C/D/E completa + casos límite | 100.020 |
| Ocho variantes A/D con protecciones + casos límite | 160.020 |

Esos totales incluyen 20 casos límite por lote y series repetidas entre variantes; **no representan esa cantidad de precios independientes**. La reproducción contable no comprueba que la señal bursátil sea rentable, que la referencia sea óptima ni que el programa pueda correr en Espino. Tampoco valida SPI: el ensayo de protocolo es separado.

Herramientas observadas: Python 3.10, Icarus Verilog/vvp 13.0. El modelo de BRAM de simulación proviene de la instalación local de Yosys 0.69. No afirmar cierre de timing basándose en estas versiones o en simulaciones funcionales.

## 11. Archivos, reproducción y lectura de trazas

### 11.1. Mapa del trabajo

| Ruta desde la raíz de desarrollo | Contenido |
|---|---|
| `tools/backtest.py` | Motor contable, cinco familias, cantidades y simulación causal |
| `tools/compare_reversion.py` | Lote A/B/C/D/E |
| `tools/compare_protections.py` | Clase Protection y lote A/D/P/F/E |
| `tools/verify_market.py` | Contraste con tarea contable oficial |
| `tests/test_backtest.py` | Pruebas de referencia y parámetros |
| `tests/test_protections.py` | Pruebas de protecciones |
| `tb/practica.csv` | Copia de la práctica de Canvas |
| `tb/tb_proyecto_4.sv` | Copia sin modificar del testbench oficial |
| `docs/estrategia/comparacion/` | Primer lote, incluyendo prefijo de 2.000 |
| `docs/estrategia/reversion_abcde/` | Segundo lote |
| `docs/estrategia/protecciones_ad/` | Tercer lote |

Cada carpeta de resultados incluye `resumen.csv`, `configuracion.json`, `RESULTADOS.md` y trazas por variante. Las de validación contable incluyen `validacion_contabilidad.json`. Los manifiestos registran hashes de la serie y versiones de fuentes de cada lote; una fuente puede haber cambiado después, por lo que debe preservarse el manifiesto histórico al repetir experimentos.

### 11.2. Comandos

Si está disponible la carpeta de desarrollo completa, ejecutar desde su raíz:

```sh
python3 -B -m unittest discover -s tests -v
make compare
make compare-reversion
make compare-protections
```

Los cálculos Python usan la biblioteca estándar. La validación contable requiere `iverilog` y `vvp`. No se programa la placa con esos comandos. Las comparaciones regeneran los archivos de su propio lote; antes de cambiar parámetros, usar otra carpeta de resultados o conservar la versión anterior para no perder evidencia.

El primer script permite `--series` y `--output`; los scripts de los dos lotes posteriores actualmente usan la práctica y sus carpetas fijadas en el código. Para evaluar otra serie con ellos hay que adaptar esas entradas o llamar al motor desde un script nuevo. Verificar siempre la longitud real del CSV: algunos títulos del primer reporte están escritos para la práctica de 20.000/2.000 precios.

Ejemplos de las llamadas de referencia que implementan una variante:

```python
from backtest import Rules, run
from compare_protections import Protection

reglas = Rules(cash=10000, commission=5)
# precios: lista de enteros 1..255, en orden temporal.

resumen_A, traza_A = run(
    precios, 'reversion_media', reglas, {'ventana': 32, 'banda': 2})

resumen_DF, traza_DF = run(
    precios, 'reversion_media', reglas, {'ventana': 32, 'banda': 1},
    Protection('F'))
```

Para AP/DP se usa `Protection('P')`; para AE/DE, `Protection('E')`. Crear una instancia NUEVA de estrategia/protección/mercado por ejecución; no reutilizar su estado entre series ni variantes. Importar desde un script dentro de `tools/` o agregar esa carpeta al entorno de importación.

### 11.3. Columnas de una traza

| Columna | Significado |
|---|---|
| `tick`, `price` | Índice y precio recibido |
| `applied_decision` | Byte calculado antes y ejecutado ahora |
| `next_decision` | Byte calculado ahora para el siguiente tick |
| `signal` | Señal de la familia base ANTES de la protección |
| `fill` | Cantidad realmente comprada, positiva, o vendida, negativa; cero si no hubo ejecución |
| `cash`, `shares`, `equity` | Caja, inventario y patrimonio después de ejecutar |
| `orders`, `commissions` | Órdenes y comisiones acumuladas |
| `max_drawdown` | Mayor caída absoluta desde máximo anterior hasta ese tick |

Los bytes de estos CSV están en decimal. El CSV que genera directamente el testbench original escribe la decisión en hexadecimal: no leer `40` de ambos formatos como si fuera lo mismo.

En variantes protegidas, `signal=+1` puede coexistir con `next_decision=0` o incluso una venta por exceso de exposición. Es intencional: la política modifica la señal base. Los contadores `events` de los resúmenes de protecciones no son comparables entre modos: P cuenta activaciones; F cuenta señales de compra bloqueadas; E cuenta decisiones limitadas o correcciones de exceso. No confundirlos con órdenes ejecutadas.

## 12. Guía para el informe si no aparece una candidata mejor

Este README permite escribir una explicación verificable de lo hecho, pero el informe final debe registrar qué variante seleccionó realmente el equipo y con qué evidencia. Estructura sugerida:

1. **Problema e interfaz:** entrada por SPI, orden para el siguiente precio, comisión, límites, plazos y contabilidad oficial.
2. **Hipótesis del algoritmo:** por qué probar reversión, qué supone sobre el mercado y dónde puede fallar.
3. **Especificación exacta:** ventana, banda, cantidades, estado inicial, calentamiento, neutral, protección si aplica y pseudocódigo. No describir solamente “usa una media móvil”.
4. **Comparación de alternativas:** los tres lotes, sus controles repetidos y las métricas observadas. Separar familias distintas, sensibilidad de parámetros y protecciones.
5. **Resultados y riesgo:** patrimonio, órdenes, comisiones y drawdown; explicar que el patrimonio incluye inventario y que el resultado es de una serie conocida.
6. **Validación:** pruebas de causalidad, contraste de contabilidad y, cuando exista, equivalencia con assembly. No presentar validación contable como validación del predictor.
7. **Generalización y limitaciones:** datos utilizados, intentos y parámetros explorados, series nuevas si se agregan, y el sesgo de haber observado varias veces la práctica.
8. **Implementación en Espino:** registros/memoria, aritmética, resolución de operaciones faltantes, IC/ciclos/CPI/tiempo promedio y peor caso. Esta sección todavía requiere trabajo nuevo.
9. **Co-diseño:** perfil de tiempo, Amdahl, dos variantes de hardware, LUTs/BRAM/frecuencia, speedup y roofline. Todavía sin resultados medidos.
10. **Selección final y reproducción:** justificar el balance elegido y dejar instrucciones y versiones que permitan reconstruirlo.

Conclusiones que los datos sí permiten: A es la mejor de estas variantes en patrimonio final sobre la práctica completa; D aumenta la actividad sin superar a A; DF ofrece un intercambio observado entre patrimonio y caída frente a D; reducir exposición o activar pánico no mejoró automáticamente el patrimonio final.

Conclusiones que no se deben escribir todavía: “A es la mejor para la presentación”, “la protección garantiza una pérdida máxima”, “cumple los tres deadlines”, “el algoritmo está acelerado en Verilog” o “se validó fuera de muestra”. Tampoco inventar costos de hardware ni tiempos a partir de lo rápido que corre Python.

## 13. Qué debe entregar el Work de la Coni al proponer una mejora

- Identificador, versión y fecha; estado propuesta/candidata/acordada.
- Regla completa y parámetros, con diferencias explícitas frente a A o D.
- Qué información pasada utiliza y qué estado mantiene.
- Referencia ejecutable, decisiones por tick y casos de prueba reproducibles.
- Todas las series de desarrollo y validación usadas, hashes o semillas, y cuáles se reservaron antes de ajustar.
- Resultados por serie y contra las mismas referencias, incluyendo casos desfavorables y comisiones.
- Explicación de por qué puede generalizar y cuáles son sus límites; sin prometer rentabilidad en la presentación.
- Operaciones y memoria que necesitará Espino; posibles cuellos de botella todavía por medir.
- Enlace a archivos/commit/pull request si puede escribir en el repositorio; si no, archivos listos para incorporar.
- Preguntas o decisiones que requieran acuerdo del equipo.

No reemplazar silenciosamente reglas comunes ni borrar los controles históricos. Si una modificación cambia simultáneamente señales, cantidades y protección, identificarla como una estrategia nueva y explicar el cambio de alcance. La versión llamada “final” seguirá siendo una candidata hasta que el equipo la evalúe y confirme.

## 14. Ampliación del 12 de noviembre: bandas por desviación e históricos reales

Se añadieron Ad y Dd, con SMA32 y bandas de 1 y 0,5 desviaciones estándar poblacionales, respectivamente. Son nuevas propuestas; A, D y DF no cambian. La especificación exacta, fuentes, normalización, límites, resultados y reproducción están en [el informe de este lote](docs/estrategia/adaptativas_2026-11-12/RESULTADOS.md). Código: `tools/compare_adaptive.py`; pruebas: `tests/test_adaptive.py`.

El lote incluye la práctica completa y sus primeros 2.000 ticks, más SPY/GOOGL/TSLA con 502 cierres diarios de 2024–2025 por activo. Los 250 cierres de 2023 solo fijan la escala propia de cada activo: `round_half_up(100 * cierre / máximo_2023)`. No se usan extremos futuros del período evaluado, no hay clipping ni puntos inventados y no se buscan parámetros después de ver el resultado. Los históricos originales JSON, metadatos y hashes quedan archivados con las trazas. Las unidades monetarias son las del juego, no retornos reales en dólares; se usa close sin sumar dividendos. La frecuencia diaria hace que 32 observaciones representen 32 sesiones, mientras que la frecuencia temporal de la práctica es desconocida.

Patrimonio final (capital inicial 10.000):

| Serie | A | D | DF | Ad | Dd | Mantener |
|---|---:|---:|---:|---:|---:|---:|
| Práctica 20.000 | 18.502 | 17.909 | 16.159 | 10.352 | 12.039 | 10.000 |
| Práctica 2.000 | 10.529 | 9.923 | 10.723 | 9.114 | 9.151 | 10.000 |
| SPY diario | 11.159 | 10.822 | 10.739 | 11.293 | 11.207 | 10.000 |
| GOOGL diario | 9.969 | 9.032 | 9.032 | 9.355 | 9.243 | 10.000 |
| TSLA diario | 11.856 | 12.858 | 14.635 | 11.717 | 13.636 | 10.000 |

El benchmark ideal de comprar y mantener del enunciado termina con 14.395, 22.418 y 17.951 en SPY, GOOGL y TSLA. Supera a todas las candidatas en estos tres períodos completos, que son alcistas entre inicio y fin. Ese benchmark compra al primer precio sin límite de 63 ni desfase, por lo que no debe presentarse como una estrategia implementada por SPI. Ad/Dd no son una mejora universal; no hay decisión final ni hard stop de patrimonio 20.000 implementado.

Validación: 25 pruebas unitarias pasan, incluidas comparación contra desviación estándar Decimal independiente, calentamiento, igualdad, invariancia ante escala/traslación de enteros sin cuantización y causalidad. La tarea contable original de Canvas concuerda en 141.056 ticks (30 corridas más casos límite); A/D/DF coinciden exactamente con las trazas anteriores. Esto sigue sin validar assembly, deadlines o FPGA para estas estrategias. Los períodos ahora explorados ya no sirven como reserva final independiente.

## 15. TSMC, NVIDIA e Intel: solo A, D y DF

Nuevo lote de 502 cierres diarios de 2024–2025 por activo. TSM corresponde al ADR estadounidense de TSMC. Las reglas de A/D/DF no cambian. [Informe completo y fuentes](docs/estrategia/semiconductores_2026-11-12/RESULTADOS.md); reproducción: `python3 tools/compare_semiconductors.py`.

TSM y NVDA desbordan 255 con la conversión anterior de nivel 100. Para no recortar sus precios, este lote usa nivel 50 para TODOS los activos: `round_half_up(50*cierre/máximo_2023)`. Se repitieron también SPY/GOOGL/TSLA con nivel 50. El cambio se decidió tras detectar el rango incompatible, sin buscar rentabilidad; la constante por activo usa solo 2023. No mezclar los patrimonios de este lote con los del nivel 100: la escala afecta bandas relativas, redondeos, comisiones e inventario. Los anteriores se conservan. No hay puntos inventados ni clipping; NVIDIA usa el histórico del proveedor en una misma base por acción para evitar confundir su split de junio de 2024 con una caída bursátil.

| Serie, nivel 50 | A | D | DF |
|---|---:|---:|---:|
| TSM | 11.872 | 12.654 | 13.171 |
| NVDA | 16.237 | 16.448 | 14.304 |
| INTC | 17.093 | 15.483 | 10.613 |
| SPY, control repetido | 11.951 | 11.330 | 10.580 |
| GOOGL, control repetido | 9.917 | 10.062 | 10.287 |
| TSLA, control repetido | 12.290 | 12.044 | 12.831 |

DF gana en TSM, D en NVDA y A en INTC; no aparece una ganadora universal. Máxima caída absoluta en TSM: A 4.124, D 4.331, DF 2.243; en NVDA: 4.781, 4.851, 4.320; en INTC: 3.615, 4.258, 917. Son 18 corridas y 20 casos límite: 9.056 ticks concordantes con la contabilidad original, y las 25 pruebas unitarias pasan. Sin hard stop ni validación de estas estrategias en Espino. Los tres activos nuevos son del mismo sector y comparten período; no son pruebas de mercado independientes.

## 16. Ampliación a 2.000 sesiones diarias por activo

Se corrieron A/D/DF sobre las últimas 2.000 fechas comunes hasta el 31-12-2025, comenzando el 18-01-2018, para los seis activos. Son casi ocho años continuos, sin reinicios de capital ni inventario entre años. El TB original tiene `NTICKS=2000` predeterminado, aunque el CSV de práctica contiene 20.000. Un tick es una observación; aquí equivale a un cierre diario y no a una transacción real de bolsa.

**Este lote es exploratorio y usa una escala distinta que conoce el máximo futuro.** Para alojar todo el recorrido de ocho años en un byte sin clipping, se eligió antes de ejecutar las estrategias `round_half_up(255*cierre/máximo_del_tramo_completo)` por activo. No se buscaron escalas para mejorar resultados, pero usar el máximo de todo el período introduce información futura en el preprocesamiento; NO describirlo como validación ciega, fuera de muestra ni completamente causal. La señal de cada candidata solo recibe el precio normalizado actual/pasado. El redondeo pierde movimientos pequeños: NVDA repite precio normalizado en 983 de las 1.999 transiciones. No mezclar estas cifras con los lotes calibrados a nivel 50/100. Los anteriores se conservan.

| Serie, 2.000 sesiones | A | D | DF |
|---|---:|---:|---:|
| SPY | 14.098 | 14.723 | 14.488 |
| GOOGL | 17.509 | 23.180 | 14.977 |
| TSLA | 11.374 | 15.282 | 7.042 |
| TSM | 13.648 | 10.013 | 11.361 |
| NVDA | 27.375 | 48.655 | 18.028 |
| INTC | 16.272 | 11.458 | 11.510 |

D gana en cuatro activos y A en dos dentro de este lote. Esto no basta para elegir D para presentación: la normalización usa datos futuros, las series comparten fechas y las caídas pueden ser grandes (D/TSLA: máxima caída absoluta 20.186). No se implementó el hard stop ni se validaron algoritmos en Espino. Las 18 corridas completas más 20 casos límite coinciden con la contabilidad Canvas en 36.020 ticks. Datos originales, hashes, decisiones y resultados: [informe del lote largo](docs/estrategia/historicos_2000_2026-11-12/RESULTADOS.md). Reproducir con `python3 tools/compare_long_history.py`.

## 17. Recomendación y prueba de salida en patrimonio 20.000

[Informe para decidir entre A/D/DF](docs/estrategia/recomendacion_2026-11-12/README.md): reúne hallazgos, gráficos SVG/PNG, escenarios, lo que se puede sostener de la transcripción y preguntas pendientes al curso. Recomendación provisional: A como base si hay que fijar una hoy; D como alternativa para maximizar patrimonio bajo oscilaciones recuperables; DF solo tras verificar que el filtro ayuda en el escenario esperado. No hay garantía entendible en la transcripción de un mercado no bajista.

Se añadió una referencia Python de salida permanente al observar patrimonio >=20.000, liquidando hasta 63 por tick al precio siguiente y sin recomprar. Si no alcanza el umbral, sigue la base. No garantiza caja final 20.000. [Resultados completos](docs/estrategia/salida_20000_2026-11-12/RESULTADOS.md): en D/TSLA mejora 15.282 → 21.819; en D/NVDA perjudica 48.655 → 20.308; en D/TB mejora 17.909 → 19.902. No es una mejora universal ni una decisión final. No se añadió al assembly de la FPGA.

La prueba compara las tres bases y sus salidas en el TB completo y seis históricos largos: 42 corridas, 192.020 ticks contrastados con Canvas incluyendo bordes. Las bases reproducen las trazas originales; donde no activa el objetivo, son idénticas. La batería actual contiene 28 pruebas unitarias. Reproducir con `python3 tools/compare_target_exit.py`; gráficos con `python3 tools/plot_findings.py` y dependencia opcional `requirements-plots.txt`. El informe central enlaza todas las fuentes y comandos.
