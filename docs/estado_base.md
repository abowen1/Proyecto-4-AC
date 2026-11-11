# Estado de la base AC4

Revisión local: 11 de noviembre de 2026. Estrategia bursátil pendiente.

## Comprobado

- Pochoco original descargado del repositorio oficial. Commit `33e8b5ae78faad7a9a36431d5ee8cf145e8573ec`.
- 13 archivos RTL y restricciones de pines idénticos al original. Reloj directo de 25 MHz.
- Ensamblador de P2 recuperado sin cambios: 10 pruebas aprobadas.
- `trade.s`: 8 instrucciones estáticas (32 bytes), lee precios y responde mantener.
- Diagnóstico SPI: 9 instrucciones estáticas (36 bytes), respuesta variable manteniendo acción 00.
- Seis simulaciones de protocolo aprobadas: 12 precios por prueba, tres períodos (10 ms, 1 ms, 0,1 ms) y dos programas. SPI a 1 MHz y arranque desfasado respecto al reloj.
- Se verifica dato recibido por la CPU, una respuesta por cada precio, ausencia de X en MISO, consumo del flag, deadline y respuesta al precio anterior.
- Programa mantener: máximo observado de 18 ciclos / 720 ns; diagnóstico: 20 ciclos / 800 ns. Ventanas de servicio desde byte_done a escritura de DECISION.
- Testbench original de Canvas: 4/4 comprobaciones aprobadas, configuración original de 2.000 precios en ronda rápida. Patrimonio 10.000, cero órdenes y cero pérdida máxima. Referencia comprar y mantener del propio testbench: 6.695. No demuestra rentabilidad de estrategia alguna.
- Verificación adicional del CSV oficial: 2.000 filas, mismos precios que la práctica, todas las decisiones 00, sin acciones y patrimonio constante.
- CSV de evidencia en `docs/evidencias/`; `resumen_spi.csv` contiene promedios y máximos. No se ejecutaron los 20.000 precios completos contra el SoC.
- Comparación posterior de cuatro estrategias de referencia Python más mantener con 20.000 precios: ver `docs/estrategia/comparacion/RESULTADOS.md`. Su contabilidad se contrastó con la tarea original de Canvas en 100.020 ejecuciones de órdenes, contando cinco series completas más casos límite. Esto no extiende la validación de ejecución del SoC a esas cuatro estrategias.

## Herramientas y bloqueo de síntesis

- Python 3.10; Icarus Verilog/vvp 13.0 (stable).
- Modelo de BRAM usado: instalación local de Yosys 0.69, `share/yosys/ice40/cells_sim.v`.
- nextpnr-ice40 responde a `--version`, pero no imprime una versión numérica útil.
- `make build` se intentó y falló al iniciar Yosys: falta `/opt/homebrew/opt/tcl-tk/lib/libtcl9.0.dylib`. La instalación visible de Tcl/Tk es 9.1.0. No se cambió la instalación del computador.
- No hay síntesis, LUTs/BRAM, frecuencia máxima ni bitstream AC4 validados todavía. El cierre de timing a 25 MHz queda pendiente.
- Icarus advierte que las imágenes HEX tienen menos de 512 palabras; se debe a que los programas ocupan 8/9 palabras. Se mantiene el comportamiento original de RAM; estas pruebas no acceden al espacio no inicializado. No silenciar ni extrapolar esta prueba al futuro uso de memoria de datos.

## Pendientes independientes de la estrategia

1. Reparar o disponer de una instalación de síntesis funcional y completar `make build`.
2. Probar en la Go Board el arranque real y el intercambio SPI; la simulación no confirma que se resolvieron los fallos físicos históricos de P2.
3. Probar con la FPGA maestra del curso.
4. Confirmar inicio/reinicio de rondas, parámetros oficiales y fecha de entrega.
5. Mantener avances y propuestas en la rama compartida `pre-entrega`; seleccionar explícitamente lo que se incorpore a `main` para evaluación. La publicación se prepara sobre la historia del repositorio del grupo y conserva el README inicial, sin force-push.

## Pendientes dependientes de la estrategia

- Reglas de decisión, cantidades, parámetros y representación numérica.
- Seleccionar o ajustar referencia Python y verificar equivalencia completa de decisiones con assembly.
- Medición del kernel bursátil y elección informada de dos alternativas de hardware.
- Rentabilidad, comisiones, drawdown, Amdahl, roofline y métricas de implementación final.
