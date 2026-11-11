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

## Herramientas y compilación: bloqueo reparado

- Python 3.10; Icarus Verilog/vvp 13.0 (stable).
- El bloqueo inicial de Yosys 0.69 con Tcl/Tk 9.1.0 se reparó reinstalando Yosys mediante Homebrew. Ahora se utiliza Yosys 0.70+post y su modelo BRAM; se repitieron las seis pruebas SPI y todas pasaron.
- nextpnr-ice40 instalado: 0.11.1_1; IceStorm: 1.1.
- `make build` terminó: mantener ocupa 1.082/1.280 celdas lógicas, 911 LUT4 y 12/16 BRAM; timing cumple a 25 MHz. Fmax estimada de esa imagen: 44,81 MHz, sin cambiar el reloj implementado.
- Se compiló y cargó también el programa original de botones/LED, con los mismos recursos y timing. Programación `VERIFY OK`; el usuario confirmó los cuatro botones y confirmó que siguen funcionando tras desconectar/reconectar USB. Los 13 archivos RTL y los programas se conservaron sin modificaciones.
- La prueba física valida el arranque y el ejemplo botones/LED a 25 MHz. SPI físico y las estrategias bursátiles siguen pendientes. Evidencia detallada en `docs/evidencias/validacion_placa_2026-11-11.md`.
- Icarus advierte que las imágenes HEX tienen menos de 512 palabras; se debe a que los programas ocupan 8/9 palabras. Se mantiene el comportamiento original de RAM; estas pruebas no acceden al espacio no inicializado. No silenciar ni extrapolar esta prueba al futuro uso de memoria de datos.

## Pendientes independientes de la estrategia

1. Probar el intercambio SPI físicamente con un emisor/maestra apropiado y luego con la FPGA maestra del curso.
2. Confirmar inicio/reinicio de rondas, parámetros oficiales y fecha de entrega.
3. Mantener avances y propuestas en la rama compartida `pre-entrega`; seleccionar explícitamente lo que se incorpore a `main` para evaluación. La publicación se prepara sobre la historia del repositorio del grupo y conserva el README inicial, sin force-push.

## Pendientes dependientes de la estrategia

**Acuerdo del 11 de noviembre:** generar series nuevas y comparar las estrategias queda para otro día, sin fecha definida. El usuario pidió expresamente no hacerlo hoy. Retomar este pendiente al planificar una próxima sesión de evaluación; no generar ni correr ese lote durante esta sesión.

- Reglas de decisión, cantidades, parámetros y representación numérica.
- Seleccionar o ajustar referencia Python y verificar equivalencia completa de decisiones con assembly.
- Medición del kernel bursátil y elección informada de dos alternativas de hardware.
- Rentabilidad, comisiones, drawdown, Amdahl, roofline y métricas de implementación final.
