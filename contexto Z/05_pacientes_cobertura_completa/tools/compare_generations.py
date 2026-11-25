"""20 corridas: cinco estrategias por cuatro CSV oficiales, sin búsqueda posterior."""
import csv,hashlib,json,os
from pathlib import Path
from backtest import ROOT,official_rules,read_prices,run,write_csv
from baltazar import Momentum,Management,CASES as PREVIOUS
from generations import CASES,ENTRY_PARAMETERS,EntryModel,EntryManagement
from verify_market import verify

TOTAL=ROOT.parents[1]
CANVAS=TOTAL/'Material de Canvas AC4'
SERIES=CANVAS/'Proyecto 4 Series Practica'
DATASETS={'Meta':CANVAS/'practica_meta.csv','AMD':SERIES/'practica_amd_2022_ene.csv',
          'Tesla':SERIES/'practica_tesla_2022.csv','Apple':SERIES/'practica_apple_2022.csv'}
COLORS={'D':'#333333','Paciente_1':'#78bda4','Paciente_2':'#007749','Lento_1':'#c28caf','Lento_2':'#882255'}

def simulate(prices,name):
    case=CASES[name];parent=PREVIOUS[case['parent']]
    if name=='D':model=policy=None
    elif case['entry']=='original':
        model=Momentum(parent['intervals'],parent['threshold'],parent['confirm'])
        policy=Management(parent)
    else:
        model=EntryModel(parent);policy=EntryManagement(parent,model,case['entry'])
    summary,rows=run(prices,'reversion_media',official_rules(),dict(ventana=32,banda=1),policy,signal_model=model)
    peak=10000;drawdown=0.
    for i,r in enumerate(rows):
        peak=max(peak,r['equity']);drawdown=max(drawdown,(peak-r['equity'])/peak)
        if policy:r.update(policy.records[i])
    summary.update(strategy=name,label=case['label'],drawdown_percent=100*drawdown)
    return summary,rows,policy

def plot(ax,dataset,traces):
    for name,case in CASES.items():
        old=name.endswith('_1')
        ax.plot(traces[(dataset,name)],label=case['label'],color=COLORS[name],
                ls='--' if old else '-',lw=1.25 if old else 1.6,alpha=.95)
    ax.axhline(10000,color='#999999',ls=':',lw=.8)
    ax.set(title=dataset+' — CSV oficial',xlabel='Tick de mercado',ylabel='Patrimonio')
    ax.grid(alpha=.15)

def main():
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    plan=dict(cases=CASES,parent_parameters={k:PREVIOUS[c['parent']] for k,c in CASES.items()},new_entry_parameters=ENTRY_PARAMETERS,
              rules=vars(rules),sources={k:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in DATASETS.items()},
              interpretation='Known official series, entry-only changes fixed before results. No grid search, no volatility/exit/exposure changes, no FPGA programming or development edits.')
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    summaries=[];traces={};validations=[]
    for dataset,path in DATASETS.items():
        prices=read_prices(path);assert len(prices)==20000
        folder=ROOT/'resultados'/dataset;folder.mkdir(parents=True,exist_ok=True);replays=[]
        for name,case in CASES.items():
            summary,rows,policy=simulate(prices,name);summary['dataset']=dataset;summaries.append(summary)
            if name in ('D','Paciente_1','Lento_1'):
                prior=ROOT.parent/'2026-11-23_Baltazar_v2/resultados'/(dataset+'_oficial')/(case['parent']+'.csv')
                old=list(csv.DictReader(prior.open()));keys=('price','applied_decision','next_decision','cash','shares','equity','orders','max_drawdown')
                assert len(old)==len(rows) and all(all(int(a[k])==b[k] for k in keys) for a,b in zip(old,rows)),'Prior generation changed'
            write_csv(folder/(name+'.csv'),rows)
            if policy:(folder/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            traces[(dataset,name)]=[r['equity'] for r in rows];replays.append((dataset+'_'+name,rows))
        print(dataset,[(x['strategy'],x['equity'],x['commissions']) for x in summaries if x['dataset']==dataset],flush=True)
        verify(replays,folder);validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
    write_csv(ROOT/'resumen.csv',summaries)
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(x['compared_ticks'] for x in validations),scope=validations[0]['scope']),indent=2))
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib');os.environ['XDG_CACHE_HOME']='/private/tmp/ac4-generaciones-cache'
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    for dataset in DATASETS:
        fig,ax=plt.subplots(figsize=(11,5.5));plot(ax,dataset,traces);ax.legend(fontsize=9,ncol=3)
        fig.tight_layout();fig.savefig(ROOT/('comparacion_'+dataset+'.png'),dpi=170);fig.savefig(ROOT/('comparacion_'+dataset+'.svg'));plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(14,9),sharex=True)
    for ax,dataset in zip(axes.flat,DATASETS):plot(ax,dataset,traces)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=5,loc='lower center',fontsize=9)
    fig.suptitle('Baltazar: generaciones 1 y 2 frente a D original — cinco curvas por serie')
    fig.tight_layout(rect=[0,.05,1,.96]);fig.savefig(ROOT/'comparacion_cuatro_series.png',dpi=170);plt.close(fig)
    scores={}
    for name in CASES:
        group=[s for s in summaries if s['strategy']==name]
        scores[name]=dict(mean_equity=sum(s['equity'] for s in group)/4,mean_commissions=sum(s['commissions'] for s in group)/4,
                         min_equity=min(s['equity'] for s in group),wins_vs_initial_cash=sum(s['equity']>10000 for s in group))
    (ROOT/'comparacion_agregada.json').write_text(json.dumps(scores,indent=2))
    (ROOT/'fuentes_sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools').glob('*.py')},indent=2))

if __name__=='__main__':main()
