"""Cuatro implementaciones,misma estrategia,78 series; conserva perfiles completos."""
import argparse,csv,hashlib,json,tarfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from backtest import ROOT,read_prices
from measure_m105_225 import compile_profile,measure

CASES={
 'base':('software','sw/trade_m105_225.s'),
 'soft':('software','sw/trade_m105_225_soft.s'),
 'shifter':('shifter','sw/trade_m105_225_shifter.s'),
 'qcap':('qcap','sw/trade_m105_225_qcap.s'),
}

def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=2);p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES));args=p.parse_args()
    manifest=json.loads((ROOT/'docs/estrategia/M105_225_implementacion/series.json').read_text())['sources']
    inputs={}
    for s in manifest:
        f=ROOT/'build/m105_225/inputs'/(s['id']+'.csv')
        if not f.exists():
            f.parent.mkdir(parents=True,exist_ok=True)
            if s['group']=='catedra':raw=(ROOT/'datos/oficiales'/s['file']).read_bytes()
            else:
                with tarfile.open(ROOT/'datos/series_recreadas_70.tar.gz','r:gz') as archive:raw=archive.extractfile(s['file']).read()
            f.write_bytes(raw)
        assert hashlib.sha256(f.read_bytes()).hexdigest()==s['sha256']
        inputs[s['id']]=read_prices(f)
    compilers={}
    for name in args.cases:
        variant,program=CASES[name];compilers[name]=compile_profile(variant,ROOT/program)
    summaries=[];completed=0
    def work(case,s):
        variant,program=CASES[case];exe,image=compilers[case]
        folder=ROOT/'build/m105_225/runs'/('profile_'+Path(program).stem+'_'+s['id'])
        prior=folder/'metrics.json';report=None
        if prior.exists() and (folder/'result.json').exists():
            previous=json.loads(prior.read_text());proof=json.loads((folder/'result.json').read_text())
            if previous['program_sha256']==hashlib.sha256(image.read_bytes()).hexdigest() and proof['price_bytes_sha256']==hashlib.sha256(bytes(inputs[s['id']])).hexdigest():
                report=previous;report['profile_reused']=True
        if report is None:
            report=measure(inputs[s['id']],s['id'],variant,ROOT/program,exe,image);report['profile_reused']=False
        for k,value in s['expected'].items():assert abs(float(report['summary'][k])-float(value))<1e-8,(case,s['id'],k)
        report.update(case=case,dataset=s['id'],group=s['group']);return report
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(work,c,s) for c in args.cases for s in manifest]
        for f in as_completed(futures):
            r=f.result();summaries.append(r);completed+=1;print(f'{completed}/{len(futures)} perfiles completos',flush=True)
    aggregates={}
    for case in args.cases:
        group=[r for r in summaries if r['case']==case];ticks=sum(r['ticks'] for r in group)
        cycles=sum(r['total_cycles'] for r in group);ic=sum(r['total_instructions'] for r in group)
        sections={}
        for r in group:
            for key,value in r['sections'].items():sections[key]=sections.get(key,0)+value
        aggregates[case]=dict(ticks=ticks,series=len(group),total_cycles=cycles,total_instructions=ic,mean_cycles=cycles/ticks,max_cycles=max(r['max_cycles'] for r in group),mean_ic=ic/ticks,max_ic=max(r['max_ic'] for r in group),cpi=cycles/ic,mean_us=cycles/ticks*.04,max_us=max(r['max_cycles'] for r in group)*.04,service_decisions_per_second=25000000/(cycles/ticks),sections=sections,words=len((ROOT/'build/m105_225_measure/compilers'/Path(CASES[case][1]).stem/'program.hex').read_text().split()),mean_equity=sum(r['summary']['equity'] for r in group)/len(group))
    out=ROOT/'build/m105_225_measure';out.mkdir(exist_ok=True)
    (out/'comparison.json').write_text(json.dumps(dict(status='PASS',strategy='M105-225',aggregates=aggregates,results=sorted(summaries,key=lambda r:(r['case'],r['dataset']))),indent=2)+'\n')
    print('FIN',json.dumps(aggregates),flush=True)

if __name__=='__main__':main()
