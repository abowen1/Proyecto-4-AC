# Validación física

Placa Go Board del equipo identificada con el número **17**, escrito a mano. Implementación: M105-225, software optimizado e ISA original de Espino, a 25 MHz.

- **24/11/2026 — Programación:** se grabó la imagen incluida en `../estrategia/M105_225_optimizacion/imagen/M105_225.bin`. El programador finalizó con `VERIFY OK` y `CDONE` alto. Registro: [programacion.log](programacion.log).
- **24/11/2026 — Persistencia:** se desconectó y reconectó la alimentación USB. La comparación de la memoria con la misma imagen, sin reprogramar, terminó con `VERIFY OK` y `CDONE` alto. Registro: [verificacion_tras_reconexion.log](verificacion_tras_reconexion.log).
- **25/11/2026 — Maestra del curso:** el equipo confirmó el arranque y el funcionamiento de la comunicación SPI y de la estrategia con la FPGA maestra. La placa había sido desconectada para su traslado. Esta comprobación es una observación física reportada por el equipo; no se midió latencia física ni se registraron por separado los tres períodos.

Los botones no reinician caja ni inventario. Las comprobaciones de períodos y plazos se documentan por simulación en las pruebas de integración.
