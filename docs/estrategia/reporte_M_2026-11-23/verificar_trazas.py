"""Reproduce decisiones y estados numéricos publicados sin regenerar gráficos."""
import argparse,csv,io,json,sys,tarfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('etapa',choices=['corto','bandas']);args=parser.parse_args()
    root=Path(__file__).resolve().parent/args.etapa
    sys.path.insert(0,str(root/'tools'))
    if args.etapa=='corto':from compare_m import simulate,DATASETS,CASES,SERIES
    else:from compare_bands import simulate,DATASETS,CASES,SERIES
    from backtest import read_prices
    summaries={(r['dataset'],r['strategy']):r for r in csv.DictReader((root/'resumen.csv').open())}
    fields=('tick','price','applied_decision','next_decision','signal','fill','cash','shares','equity','orders','commissions','max_drawdown')
    runs=ticks=0
    with tarfile.open(root/'trazas_csv.tar.gz','r:gz') as archive:
        for dataset,(_,filename) in DATASETS.items():
            prices=read_prices(SERIES/filename)
            for name in CASES:
                summary,rows,_=simulate(prices,name)
                stream=archive.extractfile(f'resultados/{dataset}/{name}.csv')
                expected=list(csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8')))
                assert len(rows)==len(expected)==20000
                assert all(all(int(a[k])==b[k] for k in fields) for a,b in zip(expected,rows)),(dataset,name,'trace mismatch')
                for k in ('equity','orders','commissions','cash','shares','max_drawdown'):
                    assert summary[k]==int(summaries[(dataset,name)][k]),(dataset,name,k)
                runs+=1;ticks+=len(rows)
    print(json.dumps(dict(status='PASS',stage=args.etapa,runs=runs,ticks=ticks,comparison='all12 numeric trace fields and6 final accounting fields')))

if __name__=='__main__':main()
