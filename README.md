# Proyecto 4 — Pochoco Trader

Implementación de **M105-225**, denominada internamente **MDIP**: software optimizado sobre la ISA original de Espino Core, en Pochoco SoC para Go Board iCE40 HX1K a **25 MHz**.

**Informe:** [Informe Proyecto 4 AC](informe/Informe_Proyecto_4_AC.pdf). El contenido de esta rama es autocontenido.

## Contenido

- [`Informe Proyecto 4 AC`](informe/Informe_Proyecto_4_AC.pdf): informe del desarrollo bursátil, la implementación y la optimización.
- `rtl/`, `sw/`, `goboard.pcf`: implementación y programa final (`sw/trade.s`, `sw/trade.hex`).
- [`imagen/`](docs/estrategia/M105_225_optimizacion/imagen/): bitstream verificado y manifiesto con hashes, recursos y timing.
- [`datos/`](datos/README.md): ocho series oficiales, 70 reconstruidas, procedencia y resumen numérico de comparación.
- [`mediciones`](docs/estrategia/M105_225_optimizacion/README.md): implementación inicial de MDIP, software optimizado, alternativas shifter y QCAP, y mediciones conservadas.
- [`verificación`](docs/estrategia/M105_225_implementacion/README.md), `tests/`, `tb/`, `tools/`: referencia Python y pruebas reproducibles.
- [`evidencia física`](docs/evidencia_fisica/README.md): programación, persistencia y funcionamiento con la maestra.
- [`enunciado original`](material/enunciado/Proyecto_4_arq.pdf).

Comprobación de esta copia de entrega: [`validacion.json`](docs/verificacion_entrega/validacion.json).

## Material de trabajo complementario

La rama [`pre-entrega`](https://github.com/abowen1/Proyecto-4-AC/tree/pre-entrega) se utilizó para la coordinación interna del equipo y para registrar avances, experimentos y resultados durante el desarrollo. Se conserva como archivo de consulta opcional para profundizar en los antecedentes o reproducir gráficos y comparaciones con los datos y herramientas allí disponibles.

**No es necesario revisar ni corregir `pre-entrega` como parte de la entrega.** El material presentado para evaluación está organizado en `main` e incluye el [Informe Proyecto 4 AC](informe/Informe_Proyecto_4_AC.pdf). Los contenidos de `pre-entrega` corresponden a distintas etapas de trabajo y pueden incluir alternativas que posteriormente fueron descartadas.

## Referencia de la estrategia

Se activa la compra con precio observado **≤105**. Se acumula con el presupuesto fijado al iniciar el episodio mientras se permanezca en esa banda; se deja de agregar al salir de ella o agotar el presupuesto. Con precio **≥225** se enclava la venta hasta liquidar el inventario. Las órdenes se fraccionan en cantidades de hasta 63. Una vez sin acciones puede comenzar otro episodio.

La decisión se ejecuta al tick siguiente. Se conservan las reglas del curso: caja inicial $10.000, comisión $5 por orden ejecutada, sin deuda ni ventas cortas. El patrimonio final es caja más inventario valorado al último precio, sin venta final forzada. La referencia ejecutable es `tools/m105_225.py`.

## Herramientas

Python 3.10 o superior (biblioteca estándar), Make, Yosys con `yosys-config`, nextpnr-ice40, IceStorm (`icepack`, `iceprog`), Icarus Verilog y Verilator con compilador C++.

Versiones utilizadas: Python 3.10.2; Yosys 0.70+post; nextpnr-ice40 0.11.1_1; IceStorm 1.1; Icarus Verilog 13.0; Verilator 5.054; Apple Clang 21.0.0. Detalles en `docs/estrategia/M105_225_optimizacion/herramientas.json`.

Ejecutar desde la raíz del repositorio:

```sh
python3 tools/reference_m105_225.py datos/oficiales/practica_meta_2022.csv
make assemble          # Ensamblar, sin conectarse a una placa
make test              # Unitarias, SPI, extensiones y programa final
make test-equivalence  # Software optimizado contra Python en las 78 series completas
make measure           # Perfil completo de Meta con el software final
make compare-implementations # Repetir la comparación de las cuatro implementaciones
make build-final       # Síntesis y place-and-route a 25 MHz; no programa la placa
```

`make test` incluye casos activos en los tres períodos (10 ms, 1 ms y 100 µs) y el testbench oficial sobre los primeros 2.000 ticks de Meta. `make test-equivalence` procesa 20.000 ticks de cada serie con el SoC completo y compara decisiones, caja e inventario con Python; acorta esperas inactivas para acelerar la simulación. No sustituye las pruebas con períodos reales.

La implementación inicial se comprueba adicionalmente con `python3 tools/test_all_m105_225.py`. Para probar integración de una alternativa: `python3 tools/test_m105_225_optimized_integration.py --case shifter --fixed` (o `--case qcap`). Los resultados nuevos se escriben en `build/`; los resultados de referencia se conservan en `docs/estrategia/`.

## Imagen y programación

La imagen incluida es `docs/estrategia/M105_225_optimizacion/imagen/M105_225.bin` (32.220 bytes). SHA-256:

```text
5be11e8803854d23bc61d15b504b2621084c08c01417fb07f629ad3abd841551
```

Con la Go Board conectada por USB, `make program-final` graba esa imagen incluida. `make build-final` permite regenerarla previamente; su salida se encuentra en `build/final/M105_225.bin`. No se seleccionan las extensiones de hardware al compilar la versión final.

Para comprobar la memoria sin reprogramar:

```sh
iceprog -c docs/estrategia/M105_225_optimizacion/imagen/M105_225.bin
```

## Conexión y comienzo de cada serie

SPI modo 0, MSB primero, reloj de hasta 1 MHz, señales de 3,3 V y tierra común. La asignación de pines se conserva en `goboard.pcf` y en el enunciado. Usar el cableado establecido por el curso con la FPGA maestra.

El estado de caja e inventario se inicializa al encender la placa; **los botones no reinician la estrategia**. Para comenzar una serie independiente, cortar y restablecer la alimentación. El reinicio interno al encendido dura 63 ciclos. La placa del equipo está identificada a mano como **17**.
