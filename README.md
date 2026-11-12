# Proyecto 4 AC — Pochoco Trader

**Decisión del equipo, 12 de noviembre: D original, reversión a la media de 32 muestras y banda 1. Sin retiro al alcanzar 20.000 ni 30.000 de patrimonio.** El programa `sw/trade.s` implementa D en Espino original; el diagnóstico mantener se conserva en `sw/hold.s`. Reglas y verificación en [implementación de D](docs/estrategia/D_implementacion.md).

Para el traspaso completo de las 15 configuraciones bursátiles exploradas, sus resultados, especificaciones y trabajo pendiente, consultar [README_ESTRATEGIAS.md](README_ESTRATEGIAS.md). Ese documento es autocontenido y se puede compartir por separado con el Work de la Coni.

**Actualización del 12 de noviembre:** [informe para decidir entre A, D y DF](docs/estrategia/recomendacion_2026-11-12/README.md), con gráficos SVG/PNG, históricos de seis activos, datos y comandos reproducibles, recomendaciones según escenario, revisión de la transcripción y prueba de salida permanente en patrimonio 20.000. Es historia exploratoria de pre-entrega, anterior a la selección de D sin techo de retiro. El informe distingue los lotes calibrados con 2023 del lote largo cuya normalización usa el máximo futuro.

## Procedencia y alcance

- Pochoco original: https://github.com/nic0villegasc/pochoco_soc
- Revisión fijada: `33e8b5ae78faad7a9a36431d5ee8cf145e8573ec`.
- Los 13 archivos de `rtl/` y los pines de la placa se conservan sin modificar.
- Reloj directo de 25 MHz; no se incorpora el divisor de P2 ni las variantes ASIC de P3.
- Se rescatan de P2 solamente el ensamblador propio y sus pruebas. El ensamblador rechaza shifts y registros fuera de x0–x15.
- `tb/tb_proyecto_4.sv` y `tb/practica.csv` son copias exactas del material de Canvas. Los originales siguen en la carpeta hermana.
- Historial y hashes en `docs/procedencia.json`; documentación del autor en `README_UPSTREAM.md`.

## Uso

Ejecutar desde esta carpeta. Requiere Python 3.10+, Icarus Verilog/vvp, Yosys (incluido `yosys-config`) y, para generar bitstream, nextpnr-ice40 e icepack. Para programar, iceprog y la Go Board.

```sh
make                 # muestra ayuda
make assemble        # genera D, mantener y diagnóstico SPI
make test            # pruebas del ensamblador y comunicación en tres períodos
make test-canvas     # testbench original: 2.000 precios, período de 0,1 ms
make test-d          # equivalencia completa D/RTL; 20.000 precios, sin espera ociosa
make test-market compare # compara cinco referencias y verifica contabilidad Canvas
make compare-reversion # compara reversión A/B/C/D/E y verifica contabilidad Canvas
make compare-protections # compara A/D con pánico, filtro y exposición
make build           # síntesis, place-and-route a 25 MHz y bitstream
make program         # carga explícita en la placa
```

`make` y las pruebas no programan la placa. El Makefile original se conserva como `Makefile.upstream`; su objetivo predeterminado sí programa y no es el que usamos para AC4.

## Programas y pruebas

- `sw/trade.s`: programa mínimo de 8 instrucciones estáticas; esperar NEW_PRICE, leer PRICE y escribir DECISION=0. No representa la estrategia final.
- `sw/spi_diagnostic.s`: diagnóstico de 9 instrucciones; devuelve `precio & 63` con acción mantener. Sirve para comprobar MISO y el desfase de una transacción.
- `tb/tb_spi_ac4.sv`: 12 precios por ejecución, incluidos 1 y 255; SPI modo 0 a 1 MHz, fase de inicio distinta del reloj; los tres períodos de ronda y ambos programas. Comprueba dato leído por CPU, una respuesta por precio, flag consumido, plazo y byte de respuesta anterior.
- `tb/tb_proyecto_4.sv`: ejemplo oficial, sin modificaciones. Deja `decisiones.csv` en la raíz.
- `build/spi_metrics_*.csv`: IC observado, ciclos, cociente ciclos/IC y latencia por precio. Resultados de simulación, no validación física.

## Medición inicial

La ventana de latencia va desde `u_spi.byte_done` hasta la escritura de DECISION. Los ciclos se cuentan a 25 MHz (40 ns). IC cuenta commits (`instr_valid_id && !stall`) observados durante esa ventana; no son líneas estáticas de assembly. El cociente ciclos/IC es de esta ventana de servicio, con polling y posibles instrucciones parcialmente solapadas en los límites; no es todavía el CPI aislado del futuro kernel bursátil.

El presupuesto conservador replica el ejemplo del curso: `(T - 9500 ns) / 40 ns`. Este testbench supone reloj directo; habrá que adaptar la medición si cambia el reloj o la microarquitectura.

## Estado y límites

Consultar `docs/estado_base.md`. La fecha final y el protocolo de inicio/reinicio de rondas siguen pendientes de confirmación del curso. No se ha conectado la maestra ni programado la placa en esta preparación.

## Coordinación

Repositorio del grupo: https://github.com/abowen1/Proyecto-4-AC

La copia local tiene `upstream` apuntando al original y `origin` al repositorio del grupo. La rama compartida de trabajo es [`pre-entrega`](https://github.com/abowen1/Proyecto-4-AC/tree/pre-entrega); `main` se reserva para preparar la entrega evaluada. Las propuestas, resultados exploratorios y contexto de los agentes se publican en `pre-entrega` hasta que el equipo seleccione qué pasa a la entrega. La carpeta local conserva su rama `ac4/base-inicial`; la publicación se prepara aparte, sobre la historia del repositorio del grupo, sin force-push.

La estrategia se documentará en `docs/estrategia/`. No es necesario escogerla para verificar esta base. Las dos alternativas de hardware exigidas por el enunciado se elegirán después de medir D.

## Comparación exploratoria

Las cuatro familias sugeridas por el enunciado y mantener están implementadas como referencias Python en `tools/backtest.py`. Reglas exactas en `docs/estrategia/comparacion.md`; resultados y trazas en `docs/estrategia/comparacion/RESULTADOS.md`. `make compare` genera resultados y reproduce las decisiones con la contabilidad original de Canvas. Esto aún no ejecuta los algoritmos bursátiles en Espino: el assembly sigue siendo mantener.

El segundo lote compara reversión A/B/C/D/E con ventanas 32/16/64/32/32 y bandas 2/2/2/1/4. A conserva la referencia original; cada otra variante cambia un solo parámetro respecto de A. Resultados, configuración, trazas completas y validación en `docs/estrategia/reversion_abcde/`. Se mantienen los resultados del primer lote.

El tercer lote compara A, D, AP, DP, AF, DF, AE y DE. P: salida por caída del precio del 10% desde máximo de la posición y espera de 32 ticks tras liquidar. F: bloquea compras con SMA8 < SMA32. E: objetivo de exposición del 50%, limita compras y vende exceso. Reglas exactas y límites en `docs/estrategia/protecciones_ad/RESULTADOS.md`. Todas siguen siendo referencias Python, sin validación de plazos de Espino.

## Material del curso

[Enunciado original de AC4 (PDF)](material/enunciado/Proyecto_4_arq.pdf), conservado sin editar y disponible también en `main`. Las fechas están pendientes de confirmación frente a los cambios del curso.
