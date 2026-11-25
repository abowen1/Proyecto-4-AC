"""Exploración fijada en plan.json antes de correr; solo series ya conocidas."""
import csv,hashlib,json,os
from pathlib import Path
from backtest import ROOT,official_rules,read_prices,run,write_csv
from baltazar import CASES,COMMON,Momentum,Management
from verify_market import verify

TOTAL=ROOT.parents[1]
CANVAS=TOTAL/'Material de Canvas AC4'
SERIES=CANVAS/'Proyecto 4 Series Practica'
RECON=TOTAL/'Investigacion generador series 2026-11-23/validacion_tres_series/v2_alineada'
DATASETS={
 'Tesla_oficial':SERIES/'practica_tesla_2022.csv',
 'AMD_oficial':SERIES/'practica_amd_2022_ene.csv',
 'Apple_oficial':SERIES/'practica_apple_2022.csv',
 'Meta_oficial':CANVAS/'practica_meta.csv',
 'Tesla_reconstruida':RECON/'TSLA/precios_reconstruidos.csv',
 'AMD_reconstruida':RECON/'AMD/precios_reconstruidos.csv',
 'Apple_reconstruida':RECON/'AAPL/precios_reconstruidos.csv',
}
def simulate(prices,name):
    cfg=CASES[name];policy=None if cfg.get('original') else Management(cfg)
    model=Momentum() if cfg['model']=='momentum' else None
    summary,rows=run(prices,'reversion_media',official_rules(),dict(ventana=32,banda=1),policy,signal_model=model)
    peak=10000;dd=0.;exposure=0.
    for i,r in enumerate(rows):
        peak=max(peak,r['equity']);dd=max(dd,(peak-r['equity'])/peak)
        exposure=max(exposure,r['shares']*r['price']/r['equity'] if r['equity'] else 0)
        if policy:r.update(policy.records[i])
    summary.update(strategy=name,label=name,drawdown_percent=100*dd,max_exposure_percent=100*exposure)
    for reason in ('stop_loss','take_profit','trailing','signal_exit'):
        summary['closed_'+reason]=sum(t['reason']==reason for t in policy.closed) if policy else None
    return summary,rows,policy

def main():
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    plan=dict(cases=CASES,common=COMMON,rules=vars(rules),
              sources={k:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in DATASETS.items()},
              interpretation='In-sample exploration on already observed official series; reconstructed twins are sensitivity checks, not independent validation',
              production_code_changed=False,fpga_programmed=False,grid_search=False)
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    summaries=[];traces={};validations=[]
    for dataset,path in DATASETS.items():
        prices=read_prices(path);assert len(prices)==20000
        folder=ROOT/'resultados'/dataset;folder.mkdir(parents=True,exist_ok=True)
        replays=[]
        for name in CASES:
            summary,rows,policy=simulate(prices,name)
            summary['dataset']=dataset;summaries.append(summary)
            if name=='D' and dataset in ('Tesla_oficial','AMD_oficial','Apple_oficial'):
                assert summary['equity']=={'Tesla_oficial':5242,'AMD_oficial':6638,'Apple_oficial':7463}[dataset]
            write_csv(folder/f'{name}.csv',rows)
            if policy:
                (folder/f'{name}_operaciones.json').write_text(json.dumps(policy.closed,indent=2))
            replays.append((dataset+'_'+name,rows))
            traces[(dataset,name)]=[r['equity'] for r in rows]
        print(dataset,[(s['strategy'],s['equity']) for s in summaries if s['dataset']==dataset],flush=True)
        verify(replays,folder)
        validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
    write_csv(ROOT/'resumen.csv',summaries)
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(v['compared_ticks'] for v in validations),datasets=len(validations),scope=validations[0]['scope']),indent=2))
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib')
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    colors=['#222222','#c2b280','#0072b2','#999999','#d55e00','#009e73','#cc79a7','#56b4e9']
    fig,axes=plt.subplots(2,2,figsize=(15,9),sharex=True)
    for ax,dataset in zip(axes.flat,list(DATASETS)[:4]):
        for (name,cfg),color in zip(CASES.items(),colors):
            ax.plot(traces[(dataset,name)],label=name,color=color,lw=1.5 if name=='D' else .95,alpha=.9)
        ax.axhline(10000,lw=.7,ls='--',color='#777777');ax.set(title=dataset.replace('_',' '),xlabel='Tick de mercado',ylabel='Patrimonio');ax.grid(alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=4,fontsize=9)
    fig.suptitle('Baltazar: primera exploración con reglas comunes y comisión fija de 5');fig.tight_layout(rect=[0,.08,1,.96]);fig.savefig(ROOT/'comparacion_oficiales.png',dpi=160)
    scores={}
    for name in CASES:
        group=[s for s in summaries if s['strategy']==name and s['dataset'].endswith('_oficial')]
        scores[name]=dict(mean_final_equity=sum(s['equity'] for s in group)/len(group),worst_final_equity=min(s['equity'] for s in group),wins_vs_cash=sum(s['equity']>10000 for s in group),mean_orders=sum(s['orders'] for s in group)/len(group),worst_drawdown_percent=max(s['drawdown_percent'] for s in group))
    (ROOT/'comparacion_agregada.json').write_text(json.dumps(scores,indent=2))
    (ROOT/'fuentes_sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools').glob('*.py')},indent=2))

if __name__=='__main__':main()
