"""Malla prefijada de 15 bandas, ocho series oficiales; sin alterar contabilidad."""
import csv, hashlib, json, os, tempfile
from pathlib import Path
from backtest import ROOT, read_prices, write_csv, run, official_rules
from m_bands import PriceSignal, BandPolicy
SERIES=ROOT.parent/'datos/oficiales'
DATASETS={
 'Meta_2022':('Meta 2022','practica_meta_2022.csv'),
 'AMD_2022_ene':('AMD enero 2022','practica_amd_2022_ene.csv'),
 'AMD_2022_may':('AMD mayo 2022','practica_amd_2022_may.csv'),
 'Tesla_2022':('Tesla enero 2022','practica_tesla_2022.csv'),
 'Apple_2022':('Apple julio 2022','practica_apple_2022.csv'),
 'Apple_2023':('Apple 2023','practica_apple_2023.csv'),
 'Netflix_2022':('Netflix 2022','practica_netflix_2022.csv'),
 'Netflix_2023':('Netflix 2023','practica_netflix_2023.csv'),
}

def simulate(prices,buy,sell):
    assert buy<sell
    cfg=dict(buy=buy,sell=sell,exposure=100);policy=BandPolicy(cfg)
    summary,rows=run(prices,'mantener',official_rules(),policy=policy,signal_model=PriceSignal(cfg))
    peak=10000;dd=0
    for i,row in enumerate(rows):
        peak=max(peak,row['equity']);dd=max(dd,(peak-row['equity'])/peak);row.update(policy.records[i])
    summary.update(strategy=f'M{buy}-{sell}',label=f'M{buy}-{sell}',buy=buy,sell=sell,exposure=100,drawdown_percent=100*dd,closed_episodes=len(policy.closed))
    return summary,rows,policy


from m_bands import COMMON
from verify_market import verify

def money(n):
    return '$'+f'{n:,.0f}'.replace(',','.')

def main():
    cases={f'M{x}-{y}':dict(buy=x,sell=y,exposure=100) for x in (105,110,115) for y in (205,210,215,220,225)}
    sources={d:dict(label=label,file=file,sha256=hashlib.sha256((SERIES/file).read_bytes()).hexdigest()) for d,(label,file) in DATASETS.items()}
    (ROOT/'protocolo.json').write_text(json.dumps(dict(cases=cases,common=COMMON,sources=sources,initial_cash=10000,commission_per_executed_order=5,execution='Next tick; no final liquidation',selection='Equal weight arithmetic mean across eight known series; not independent validation'),indent=2,ensure_ascii=False))
    os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'ac4-M-mpl'))
    os.environ.setdefault('XDG_CACHE_HOME',str(Path(tempfile.gettempdir())/'ac4-M-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    colors=['#0072b2','#e69f00','#009e73','#cc79a7','#882255']
    styles=['-','--',':']
    summaries=[];checks=[];curves={}
    (ROOT/'graficos').mkdir(exist_ok=True)
    for d,(label,file) in DATASETS.items():
        prices=read_prices(SERIES/file)
        assert len(prices)==20000
        dest=ROOT/'resultados'/d;dest.mkdir(parents=True,exist_ok=True)
        replays=[]
        fig,ax=plt.subplots(figsize=(12,7.8))
        for i,(name,cfg) in enumerate(cases.items()):
            summary,rows,policy=simulate(prices,cfg['buy'],cfg['sell'])
            summary['dataset']=d;summaries.append(summary)
            write_csv(dest/(name+'.csv'),rows)
            (dest/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            replays.append((d+'_'+name,rows));curves[d,name]=[r['equity'] for r in rows]
            ax.plot(range(1,20001),curves[d,name],color=colors[i%5],ls=styles[i//5],lw=1.4,alpha=.9,label=f'{name} · {money(summary["equity"])}')
        verify(replays,dest)
        checks.append(json.loads((dest/'validacion_contabilidad.json').read_text()))
        ax.axhline(10000,color='#777777',ls='-.',lw=.8)
        ax.set(title=label+' | 15 variantes M',xlabel='Tick de mercado',ylabel='Patrimonio ($)',xlim=(1,20000))
        ax.grid(alpha=.18)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:,.0f}'.replace(',','.')))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:,.0f}'.replace(',','.')))
        ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.14),fontsize=10,frameon=False,columnspacing=2,handlelength=3)
        fig.suptitle('Compra hasta X / vende desde Y · Leyenda: patrimonio final a los 20.000 ticks',fontsize=11,y=.95)
        fig.subplots_adjust(left=.09,right=.98,top=.88,bottom=.32)
        fig.savefig(ROOT/'graficos'/(d+'.png'),dpi=160)
        plt.close(fig)
        print(label,[(s['strategy'],s['equity']) for s in summaries if s['dataset']==d],flush=True)
    write_csv(ROOT/'resumen.csv',summaries)
    stats=[]
    for name,cfg in cases.items():
        group=[s for s in summaries if s['strategy']==name]
        stats.append(dict(strategy=name,**cfg,mean_equity=sum(s['equity'] for s in group)/8,min_equity=min(s['equity'] for s in group),wins_vs_initial=sum(s['equity']>10000 for s in group),mean_commissions=sum(s['commissions'] for s in group)/8,max_drawdown_percent=max(s['drawdown_percent'] for s in group)))
    stats.sort(key=lambda r:r['mean_equity'],reverse=True)
    write_csv(ROOT/'ranking.csv',stats)
    (ROOT/'agregados.json').write_text(json.dumps(stats,indent=2))
    (ROOT/'validacion.json').write_text(json.dumps(dict(status='PASS',simulations=len(summaries),compared_ticks=sum(c['compared_ticks'] for c in checks),official_series=8,strategy_variants=15),indent=2))
    print('RANKING',json.dumps(stats),flush=True)

if __name__=='__main__':
    main()
