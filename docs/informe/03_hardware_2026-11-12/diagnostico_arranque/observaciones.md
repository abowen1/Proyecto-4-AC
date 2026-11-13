# Observaciones de arranque

Los resultados fisicos se conservan sin reinterpretarlos como una causa electrica demostrada.

1. Diagnostico shifter, reset inicial 15 ciclos: usuario informa un LED y EE. Nueva version detallada: E3, comprobacion de 255<<5 frente a 8160.
2. Programa de lectura: tras una programacion llega a A5; tras quitar alimentacion entra en lectura de valores. Usuario lee actual bajo=00, actual alto=00, esperado bajo=E0, esperado alto=1F. Resultado real 0, esperado 8160.
3. Stress 1001 repeticiones: usuario informa LED apagados y displays 00; no llega al marcador de termino. No se interpreta ese 00 como un contador valido de cero fallos.
4. UART con captura de primera escritura x5: tras programar se obtiene operando 255 y resultado 8160. Tras quitar alimentacion se obtiene DEAD_BEEF, marcador de ausencia de captura dentro de 256 ciclos; no es un resultado del ALU.
5. Captura UART de primera instruccion, reset 15, trama de cabecera completa: 0x00008000 frente a programa 0x800000B7. La captura equivalente pasa en RTL. Por separado, el autodiagnostico de calculos pasa tanto en la netlist sintetizada como en la extraida del ruteo. El archivo trace_opcode_robust_warm.txt conserva la lectura cruda.
6. Reset experimental 63 ciclos: UART obtiene primera instruccion correcta 0x800000B7 tras programar. Confirmado tambien en frio. Los autodiagnosticos completos de ambos disenos pasan tras programar y tras desconectar/reconectar; ver prueba_placa.md y placa.json.

Las capturas antiguas con cabecera de un solo byte son menos robustas; no se usan los paquetes ambiguos para justificar una causa. El transmisor nuevo usa 55 AA 12 34 y se verifica con un receptor de prueba RTL. Las mediciones previas al cambio de reset se archivaron como provisionales; la comparación final ya repite las nueve corridas con reset común de 63 ciclos.
