"""40 corridas oficiales con Martín1-5; parámetros fijados antes de evaluar."""
import hashlib,json,os
from backtest import ROOT,official_rules,read_prices,run,write_csv
from martin_bands import CASES,COMMON,PriceSignal,BandPolicy
from verify_market import verify

SERIES=ROOT.parent/'datos/oficiales'
DATASETS={
 'Meta_2022':('Meta 2022','practica_meta_2022.csv'),
 'AMD_2022_ene':('AMD enero 2022','practica_amd_2022_ene.csv'),
 'AMD_2022_may':('AMD mayo 2022','practica_amd_2022_may.csv'),
 'Tesla_2022':('Tesla 2022','practica_tesla_2022.csv'),
 'Apple_2022':('Apple julio 2022','practica_apple_2022.csv'),
 'Apple_2023':('Apple 2023','practica_apple_2023.csv'),
 'Netflix_2022':('Netflix 2022','practica_netflix_2022.csv'),
 'Netflix_2023':('Netflix 2023','practica_netflix_2023.csv'),
}
COLORS={'Martin_1':'#0072b2','Martin_2':'#e69f00','Martin_3':'#009e73','Martin_4':'#cc79a7','Martin_5':'#882255'}

def simulate(prices,name):
    cfg=CASES[name];policy=BandPolicy(cfg)
    summary,rows=run(prices,'mantener',official_rules(),policy=policy,signal_model=PriceSignal(cfg))
    peak=10000;dd=0;exposure=0
    for i,r in enumerate(rows):
        peak=max(peak,r['equity']);dd=max(dd,(peak-r['equity'])/peak)
        if r['equity']:exposure=max(exposure,r['shares']*r['price']/r['equity'])
        r.update(policy.records[i])
    summary.update(strategy=name,label='Martín '+name[-1],drawdown_percent=100*dd,max_exposure_percent=100*exposure,closed_episodes=len(policy.closed))
    return summary,rows,policy

def main():
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    assert {p.name for p in SERIES.glob('*.csv')}=={s[1] for s in DATASETS.values()}
    plan=dict(cases=CASES,common=COMMON,rules=vars(rules),sources={k:dict(label=v[0],file=v[1],sha256=hashlib.sha256((SERIES/v[1]).read_bytes()).hexdigest()) for k,v in DATASETS.items()},
              interpretation='Exploratory on8 known official series; plausible band hypothesis from photographs, not identification of Norton code. No search after results.',production_code_changed=False,fpga_programmed=False)
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False));(ROOT/'graficos').mkdir(exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib');os.environ['XDG_CACHE_HOME']='/private/tmp/ac4-martin-bands-cache'
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    fmt=FuncFormatter(lambda x,pos:f'{x:,.0f}'.replace(',','.'))
    summaries=[];validations=[];curves={}
    for d,(label,file) in DATASETS.items():
        prices=read_prices(SERIES/file);assert len(prices)==20000
        folder=ROOT/'resultados'/d;folder.mkdir(parents=True,exist_ok=True);replays=[]
        for name in CASES:
            summary,rows,policy=simulate(prices,name);summary['dataset']=d;summaries.append(summary)
            write_csv(folder/(name+'.csv'),rows);(folder/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            curves[(d,name)]=[r['equity'] for r in rows];replays.append((d+'_'+name,rows))
        verify(replays,folder);validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
        fig,ax=plt.subplots(figsize=(11,5))
        for name in CASES:ax.plot(curves[(d,name)],label='Martín '+name[-1],color=COLORS[name],lw=1.4,ls='--' if name=='Martin_2' else '-')
        ax.axhline(10000,ls=':',color='#888888',lw=.8);ax.set(title=label+' - CSV oficial',xlabel='Tick de mercado',ylabel='Patrimonio');ax.legend(ncol=5,fontsize=9);ax.grid(alpha=.15)
        ax.xaxis.set_major_formatter(fmt);ax.yaxis.set_major_formatter(fmt);fig.tight_layout();fig.savefig(ROOT/'graficos'/(d+'.png'),dpi=170);plt.close(fig)
        print(label,[(s['strategy'],s['equity'],s['orders']) for s in summaries if s['dataset']==d],flush=True)
    write_csv(ROOT/'resumen.csv',summaries)
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(v['compared_ticks'] for v in validations),runs=40,scope=validations[0]['scope']),indent=2))
    stats={}
    for name in CASES:
        rr=[s for s in summaries if s['strategy']==name]
        stats[name]=dict(mean_equity=sum(s['equity'] for s in rr)/8,min_equity=min(s['equity'] for s in rr),wins_vs_initial=sum(s['equity']>10000 for s in rr),
                         mean_orders=sum(s['orders'] for s in rr)/8,mean_commissions=sum(s['commissions'] for s in rr)/8,max_drawdown_percent=max(s['drawdown_percent'] for s in rr))
    (ROOT/'agregados.json').write_text(json.dumps(stats,indent=2))
    items=list(DATASETS.items())
    for batch in range(2):
        fig,axes=plt.subplots(2,2,figsize=(14,8.5))
        for ax,(d,(label,_)) in zip(axes.flat,items[batch*4:batch*4+4]):
            for n in CASES:ax.plot(curves[(d,n)],label='Martín '+n[-1],color=COLORS[n],lw=1.2,ls='--' if n=='Martin_2' else '-')
            ax.axhline(10000,ls=':',color='#888888',lw=.7);ax.set(title=label,xlabel='Tick de mercado',ylabel='Patrimonio');ax.grid(alpha=.15);ax.xaxis.set_major_formatter(fmt);ax.yaxis.set_major_formatter(fmt)
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=5,loc='lower center');fig.suptitle('Martín 1-5: bandas amplias, ocho CSV oficiales, comisión fija5')
        fig.tight_layout(rect=[0,.05,1,.96]);fig.savefig(ROOT/'graficos'/f'panel_{batch+1}.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
