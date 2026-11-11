"""Sensibilidad de reversión: A base; B/C cambian ventana; D/E cambian banda."""
from pathlib import Path
import csv
import hashlib
import json
from backtest import ROOT, official_rules, read_prices, run, write_csv
from verify_market import verify

VARIANTS = {
    'A': {'ventana': 32, 'banda': 2},
    'B': {'ventana': 16, 'banda': 2},
    'C': {'ventana': 64, 'banda': 2},
    'D': {'ventana': 32, 'banda': 1},
    'E': {'ventana': 32, 'banda': 4},
}


def main():
    destination = ROOT / 'docs/estrategia/reversion_abcde'
    destination.mkdir(parents=True, exist_ok=True)
    series = ROOT / 'tb/practica.csv'
    prices, rules = read_prices(series), official_rules()
    summaries, replays = [], []
    for name, parameters in VARIANTS.items():
        summary, rows = run(prices, 'reversion_media', rules, parameters)
        summary.update(strategy='reversion_' + name, label='Reversión ' + name, **parameters)
        summaries.append(summary)
        replays.append((name, rows))
        write_csv(destination / f'reversion_{name}.csv', rows)
    # A debe reproducir exactamente la variante de la comparación anterior.
    previous = ROOT / 'docs/estrategia/comparacion/completa_reversion_media.csv'
    if previous.exists():
        original = list(csv.DictReader(previous.open()))
        assert len(original) == len(replays[0][1])
        assert all({key: int(value) for key, value in old.items()} == new
                   for old, new in zip(original, replays[0][1]))
    write_csv(destination / 'resumen.csv', summaries)
    verify(replays, destination)
    manifest = dict(variants=VARIANTS, rules=vars(rules), ticks=len(prices),
                    series_sha256=hashlib.sha256(series.read_bytes()).hexdigest(),
                    source_sha256={f: hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                                   for f in ('backtest.py','compare_reversion.py','verify_market.py')},
                    protocol='Orden calculada en n se ejecuta en n+1; sin liquidación final',
                    quantities='Misma política: comprar con caja disponible y vender inventario; máximo 63 por orden',
                    scope='Comparación exploratoria sobre la misma serie, sin validar deadlines FPGA')
    (destination/'configuracion.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    report = ['# Reversión A, B, C, D y E', '',
              'Mismos 20.000 precios, caja inicial 10.000 y comisión 5. Parámetros seleccionados antes de correr este lote, cambiando una variable por vez respecto de A.', '',
              '| Variante | Ventana (ticks) | Banda (precio) | Patrimonio final | Órdenes | Comisiones | Drawdown máximo |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for r in summaries:
        report.append(f"| {r['label']} | {r['ventana']} | {r['banda']} | {r['equity']} | {r['orders']} | {r['commissions']} | {r['max_drawdown']} |")
        print(f"{r['label']}: ventana={r['ventana']}, banda={r['banda']}, patrimonio={r['equity']}, órdenes={r['orders']}, comisión={r['commissions']}, drawdown={r['max_drawdown']}")
    report += ['', 'A conserva exactamente la variante original. B/C cambian solo la ventana; D/E cambian solo la banda.', '',
               'Compra cuando promedio − precio > banda; vende cuando promedio − precio < −banda; dentro de la banda mantiene la posición. La ventana incluye el precio actual. Espera a llenar la ventana antes de operar. Se usan comparaciones enteras sin redondear el promedio.', '',
               'Se mantiene el desfase de un precio y la misma política de cantidades que en la primera comparación. Los montos ya incluyen comisiones y valoran acciones remanentes al precio final. No hay ventas en corto, deuda ni liquidación forzada al terminar.', '',
               'La contabilidad se compara por tick con la tarea original de Canvas. Esto no implementa las variantes en assembly ni mide si cumplen el plazo. Todas usan la misma serie conocida: una ganadora aquí no demuestra que lo sea en otras series.', '',
               'Reproducir: `make compare-reversion`. No se sobrescriben los resultados del lote anterior.']
    (destination/'RESULTADOS.md').write_text('\n'.join(report)+'\n')


if __name__ == '__main__':
    main()
