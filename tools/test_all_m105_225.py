"""78 SoC completos independientes contra la referencia seleccionada."""
import argparse, hashlib, json, tarfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from backtest import ROOT,read_prices
from verify_m105_225 import compile_simulator,verify

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',choices=['iverilog','verilator'],default='verilator');p.add_argument('--workers',type=int,default=2);args=p.parse_args()
    manifest=json.loads((ROOT/'docs/estrategia/M105_225_implementacion/series.json').read_text())
    source=ROOT/'build/m105_225/inputs';source.mkdir(parents=True,exist_ok=True)
    exe=compile_simulator(args.engine)
    jobs=[]
    for s in manifest['sources']:
        local=ROOT.parent/('series recreadas' if s['group']=='recreada' else 'Material de Canvas AC4/Proyecto 4 Series Practica')/s['file']
        if local.exists():data=local.read_bytes()
        elif s['group']=='catedra':data=(ROOT/'docs/estrategia/reporte_M_2026-11-23/datos/oficiales'/s['file']).read_bytes()
        else:
            with tarfile.open(ROOT/'docs/estrategia/seleccion_M105_225_2026-11-24/datos/series_recreadas_70.tar.gz','r:gz') as archive:data=archive.extractfile(s['file']).read()
        assert hashlib.sha256(data).hexdigest()==s['sha256']
        f=source/(s['id']+'.csv');f.write_bytes(data);jobs.append((s,read_prices(f)))
    reports=[]
    def task(job):
        s,prices=job;r=verify(prices,s['id'],exe)
        assert len(prices)==20000
        for k,value in s['expected'].items():assert abs(float(r['summary'][k])-float(value))<1e-8,(s['id'],k)
        r.update(dataset=s['id'],csv_sha256=s['sha256'],group=s['group']);return r
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(task,job) for job in jobs]
        for f in as_completed(futures):
            reports.append(f.result());print(f'{len(reports)}/78 completas',flush=True)
    output=dict(status='PASS',strategy='M105-225',engine=args.engine,series=78,ticks=sum(r['ticks'] for r in reports),
                program_sha256=reports[0]['program_sha256'],all_results_match_selected_comparison=True,
                scope='Complete original SoC RTL with real SPI transactions, idle gaps shortened only. No synthesis or physical programming.',results=sorted(reports,key=lambda r:r['dataset']))
    (ROOT/'build/m105_225/equivalencia_78.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS:78 series completas,1560000 ticks en SoC RTL',flush=True)

if __name__=='__main__':main()
