# Referencias de verificación M105-225

`series.json` identifica las 78 entradas y los resultados esperados; `resultados_78.csv` resume patrimonio, órdenes y comisiones. `equivalencia_78.json` conserva la comparación completa de la implementación inicial (85 palabras) con Python: 78 series y 1.560.000 ticks.

`casos_tecnicos.json`, `integracion_tres_periodos.json`, `canvas_meta_2000.json` y los registros asociados conservan los resultados de casos técnicos, SPI y testbench oficial. La verificación de la versión optimizada se conserva en la carpeta hermana `M105_225_optimizacion`.

Para repetir: `make test`, `make test-equivalence`. Para la implementación inicial: `python3 tools/test_all_m105_225.py`. Las nuevas salidas quedan en `build/`.
