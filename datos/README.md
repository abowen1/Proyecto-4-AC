# Series y referencia numérica

- `oficiales/`: ocho CSV oficiales, 20.000 precios cada uno, conservados sin modificar.
- `series_recreadas_70.tar.gz`: 70 CSV, 14 por acción (Meta, Apple, Netflix, AMD y Tesla), 20.000 precios por serie. Para extraer: `tar -xzf datos/series_recreadas_70.tar.gz -C destino` (crear antes el directorio de destino).
- `procedencia.json`: URLs de las fuentes públicas, calendario, hashes y cobertura de minutos.
- `indice_series_recreadas.json`: períodos, archivos, hashes y datos de normalización de las series reconstruidas, entre 2022 y 2024.
- `comparacion_finalistas_78.csv`: resultados guardados de las cuatro configuraciones finalistas sobre las mismas 78 series.
- `../docs/estrategia/M105_225_implementacion/series.json`: identificadores, hashes de entrada y resultados esperados de M105-225 en las 78 series.
- `../docs/estrategia/M105_225_implementacion/resultados_78.csv`: resumen de la configuración definitiva.

Las reconstrucciones usan cierres públicos por minuto del conjunto Syncster en Hugging Face, filtrados a la sesión regular de Nueva York, con 20.000 observaciones consecutivas por bloque y sin interpolación. Se normaliza cada bloque por separado con NumPy float64: `np.rint(100 + 155*(close-min)/(max-min))`. Las reconstrucciones no se presentan como copias exactas del generador de la cátedra. El índice conserva la procedencia y metadatos originales.

La referencia de la estrategia es `tools/m105_225.py`; `make test-equivalence` verifica sus resultados frente al software final ejecutado en el SoC RTL.
