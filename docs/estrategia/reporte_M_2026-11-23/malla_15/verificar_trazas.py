"""Comprueba el código publicable contra las 120 trazas originales comprimidas."""
import csv, hashlib, io, json, sys, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from compare_grid import DATASETS, SERIES, simulate
from m_bands import CASES
from backtest import read_prices

def main():
    protocol = json.loads((ROOT / 'protocolo.json').read_text())
    assert CASES == protocol['cases']
    summaries = {(r['dataset'], r['strategy']): r for r in csv.DictReader((ROOT / 'resumen.csv').open())}
    numeric = ('tick','price','applied_decision','next_decision','signal','fill','cash','shares','equity','orders','commissions','max_drawdown')
    metadata = ('state','reason','episode_budget','acquisition_cost')
    count = ticks = 0
    with tarfile.open(ROOT / 'trazas_csv.tar.gz', 'r:gz') as archive:
        for dataset, (_, filename) in DATASETS.items():
            assert hashlib.sha256((SERIES / filename).read_bytes()).hexdigest() == protocol['sources'][dataset]['sha256']
            prices = read_prices(SERIES / filename)
            for name, cfg in CASES.items():
                summary, rows, policy = simulate(prices, cfg['buy'], cfg['sell'])
                stream = archive.extractfile(f'resultados/{dataset}/{name}.csv')
                expected = list(csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8')))
                assert len(rows) == len(expected) == 20000
                assert all(all(int(a[k]) == b[k] for k in numeric) and
                           all(str(a[k]) == str(b[k]) for k in metadata)
                           for a, b in zip(expected, rows)), (dataset, name, 'trace')
                for k in ('equity','orders','commissions','cash','shares','max_drawdown','closed_episodes'):
                    assert summary[k] == int(summaries[dataset, name][k]), (dataset, name, k)
                episodes = json.load(archive.extractfile(f'resultados/{dataset}/{name}_operaciones.json'))
                assert policy.closed == episodes
                count += 1
                ticks += len(rows)
            print('PASS', dataset, flush=True)
    result = dict(status='PASS',runs=count,ticks=ticks,source_hashes_checked=8,
                  comparison='All12 numeric columns,4 policy columns,7 final fields and closed episodes; no graph changes')
    (ROOT / 'verificacion_reproduccion.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__ == '__main__':
    main()
