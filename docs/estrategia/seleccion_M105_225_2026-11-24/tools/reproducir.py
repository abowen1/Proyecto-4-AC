"""Referencia seleccionada M105-225;78 entradas locales, sin red ni FPGA."""
import argparse, csv, hashlib, io, json, math, sys, tarfile
from pathlib import Path
from backtest import ROOT, official_rules, run, write_csv
from m_bands import BandPolicy, PriceSignal

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--todas',action='store_true',help='Reproduce las cuatro finalistas:312 corridas, en vez de78 de la elegida.')
    parser.add_argument('--trazas',type=Path,help='Guarda las trazas por tick y campañas cerradas en esta carpeta.')
    args=parser.parse_args()
    plan=json.loads((ROOT/'plan.json').read_text())
    selected=['M105-225'] if not args.todas else list(plan['cases'])
    expected={(r['dataset'],r['strategy']):r for r in csv.DictReader((ROOT/'resumen.csv').open())}
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    runs=ticks=0
    with tarfile.open(ROOT/'datos/series_recreadas_70.tar.gz','r:gz') as archive:
        assert len([m for m in archive.getmembers() if m.isfile()])==70
        for s in plan['sources']:
            if s['group']=='recreada':
                data=archive.extractfile(s['file']).read()
            else:
                data=(ROOT.parent/'reporte_M_2026-11-23/datos/oficiales'/s['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==s['sha256'],s['id']
            raw=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
            assert len(raw)==20000 and [int(r['tick']) for r in raw]==list(range(20000))
            prices=[int(r['price']) for r in raw]
            assert min(prices)==100 and max(prices)==255
            for name in selected:
                cfg=plan['cases'][name];policy=BandPolicy(cfg)
                summary,rows=run(prices,'mantener',rules,policy=policy,signal_model=PriceSignal(cfg))
                exp=expected[s['id'],name]
                for k in ('equity','profit','cash','shares','orders','commissions','max_drawdown'):
                    assert summary[k]==int(exp[k]),(s['id'],name,k)
                peak=10000;dd=0
                for row in rows:
                    peak=max(peak,row['equity']);dd=max(dd,(peak-row['equity'])/peak)
                assert math.isclose(dd*100,float(exp['drawdown_percent']),abs_tol=1e-10)
                assert len(policy.closed)==int(exp['closed_episodes'])
                if args.trazas:
                    dest=args.trazas/s['id'];dest.mkdir(parents=True,exist_ok=True)
                    for row,record in zip(rows,policy.records):row.update(record)
                    write_csv(dest/(name+'.csv'),rows)
                    (dest/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
                runs+=1;ticks+=len(rows)
            print('PASS',s['id'],flush=True)
    result=dict(status='PASS',strategy='four_finalists' if args.todas else 'M105-225',runs=runs,ticks=ticks,
                source_hashes_checked=78,comparison='Seven final accounting fields,percentage drawdown and closed episode count versus saved results; same frozen policy classes',
                scope='Python reference reproduction; no assembly, RTL, timing or physical validation')
    path=ROOT/('verificacion_cuatro_finalistas.json' if args.todas else 'verificacion_referencia.json')
    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
