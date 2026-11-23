"""24 corridas: solo tres configuraciones de Martín y ocho CSV oficiales."""
import json,hashlib,os
from pathlib import Path
from backtest import ROOT,official_rules,read_prices,run,write_csv
from martin import CASES,COMMON,ShortSignal,FixedHolding
from verify_market import verify

SERIES=ROOT.parent/'datos/oficiales'
DATASETS={
 'Meta_2022':('Meta 2022','practica_meta_2022.csv'),
 'AMD_2022_ene':('AMD enero 2022','practica_amd_2022_ene.csv'),
 'AMD_2022_may':('AMD mayo 2022','practica_amd_2022_may.csv'),
 'Tesla_2022':('Tesla 2022','practica_tesla_2022.csv'),
 'Apple_2022':('Apple 2022','practica_apple_2022.csv'),
 'Apple_2023':('Apple 2023','practica_apple_2023.csv'),
 'Netflix_2022':('Netflix 2022','practica_netflix_2022.csv'),
 'Netflix_2023':('Netflix 2023','practica_netflix_2023.csv'),
}
COLORS={'Martin_A':'#0072b2','Martin_B':'#009e73','Martin_C':'#cc79a7'}

def simulate(prices,name):
    cfg=CASES[name];policy=FixedHolding(cfg['holding'])
    summary,rows=run(prices,'mantener',official_rules(),policy=policy,
                     signal_model=ShortSignal(cfg['lookback'],cfg['threshold']))
    peak=10000;dd=0
    for i,row in enumerate(rows):
        peak=max(peak,row['equity']);dd=max(dd,(peak-row['equity'])/peak);row.update(policy.records[i])
    summary.update(strategy=name,label=name.replace('_',' '),drawdown_percent=100*dd,closed_trades=len(policy.closed),
                   winning_trades=sum(t['net_profit']>0 for t in policy.closed),holding=cfg['holding'])
    return summary,rows,policy

def main():
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    assert {p.name for p in SERIES.glob('*.csv')}=={x[1] for x in DATASETS.values()}
    plan=dict(cases=CASES,common=COMMON,rules=vars(rules),sources={k:dict(label=v[0],file=v[1],sha256=hashlib.sha256((SERIES/v[1]).read_bytes()).hexdigest()) for k,v in DATASETS.items()},
              scope='Exactly eight official inputs, three configurations fixed before results. No recreated data, no reoptimization after observing scores, no PDF report or firmware changes.')
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False));(ROOT/'graficos').mkdir(exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib');os.environ['XDG_CACHE_HOME']='/private/tmp/ac4-martin-cache'
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    money=FuncFormatter(lambda x,pos:f'{x:,.0f}'.replace(',','.'))
    all_summaries=[];validations=[];curves={}
    for dataset,(label,file) in DATASETS.items():
        prices=read_prices(SERIES/file);assert len(prices)==20000
        folder=ROOT/'resultados'/dataset;folder.mkdir(parents=True,exist_ok=True);replays=[]
        for name in CASES:
            summary,rows,policy=simulate(prices,name);summary['dataset']=dataset;all_summaries.append(summary)
            write_csv(folder/(name+'.csv'),rows);(folder/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            curves[(dataset,name)]=[r['equity'] for r in rows];replays.append((dataset+'_'+name,rows))
        verify(replays,folder);validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
        fig,ax=plt.subplots(figsize=(10.5,4.7))
        for name in CASES:ax.plot(curves[(dataset,name)],label='Martín '+name[-1],color=COLORS[name],lw=1.2)
        ax.axhline(10000,color='#888888',ls=':',lw=.8);ax.set(title=label+' - CSV oficial',xlabel='Tick de mercado',ylabel='Patrimonio')
        ax.legend(ncol=3,frameon=False);ax.grid(alpha=.15);ax.xaxis.set_major_formatter(money);ax.yaxis.set_major_formatter(money)
        fig.tight_layout();fig.savefig(ROOT/'graficos'/(dataset+'.png'),dpi=160);plt.close(fig)
        print(label,[(s['strategy'],s['equity'],s['commissions']) for s in all_summaries if s['dataset']==dataset],flush=True)
    write_csv(ROOT/'resumen.csv',all_summaries)
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(x['compared_ticks'] for x in validations),runs=24,scope=validations[0]['scope']),indent=2))
    stats={}
    for n in CASES:
        rr=[r for r in all_summaries if r['strategy']==n]
        stats[n]=dict(mean_equity=sum(r['equity'] for r in rr)/8,worst_equity=min(r['equity'] for r in rr),wins_vs_initial=sum(r['equity']>10000 for r in rr),
                      mean_commissions=sum(r['commissions'] for r in rr)/8,mean_orders=sum(r['orders'] for r in rr)/8,max_drawdown_percent=max(r['drawdown_percent'] for r in rr))
    (ROOT/'agregados.json').write_text(json.dumps(stats,indent=2))
    # Mismo resultado, vista compacta de cuatro gráficos por imagen para el chat.
    items=list(DATASETS.items())
    for batch in range(2):
        fig,axes=plt.subplots(2,2,figsize=(13,8))
        for ax,(d,(label,_)) in zip(axes.flat,items[batch*4:batch*4+4]):
            for n in CASES:ax.plot(curves[(d,n)],label='Martín '+n[-1],color=COLORS[n],lw=1.1)
            ax.axhline(10000,color='#888888',ls=':',lw=.7);ax.set(title=label,xlabel='Tick de mercado',ylabel='Patrimonio');ax.grid(alpha=.15)
            ax.xaxis.set_major_formatter(money);ax.yaxis.set_major_formatter(money)
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3)
        fig.suptitle('Martín A, B y C - ocho series oficiales, comisión fija 5');fig.tight_layout(rect=[0,.05,1,.96]);fig.savefig(ROOT/'graficos'/f'panel_{batch+1}.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
