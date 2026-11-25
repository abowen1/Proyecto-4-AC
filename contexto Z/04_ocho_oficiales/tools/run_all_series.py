"""40 corridas con estrategias congeladas; solo los ocho CSV oficiales de la carpeta."""
import csv,hashlib,json,os
from pathlib import Path
from backtest import ROOT,official_rules,read_prices,write_csv
from generations import CASES,ENTRY_PARAMETERS
from baltazar import CASES as PARENTS
from compare_generations import simulate
from verify_market import verify

SERIES=ROOT.parents[1]/'Material de Canvas AC4/Proyecto 4 Series Practica'
DATASETS={
 'Meta_2022':('Meta 2022','practica_meta_2022.csv','Meta'),
 'AMD_2022_ene':('AMD 2022 - enero','practica_amd_2022_ene.csv','AMD'),
 'AMD_2022_may':('AMD 2022 - mayo','practica_amd_2022_may.csv',None),
 'Tesla_2022':('Tesla 2022','practica_tesla_2022.csv','Tesla'),
 'Apple_2022':('Apple 2022','practica_apple_2022.csv','Apple'),
 'Apple_2023':('Apple 2023','practica_apple_2023.csv',None),
 'Netflix_2022':('Netflix 2022','practica_netflix_2022.csv',None),
 'Netflix_2023':('Netflix 2023','practica_netflix_2023.csv',None),
}
LABELS={'D':'D original','Paciente_1':'Paciente 1','Paciente_2':'Paciente 2','Lento_1':'Lento 1','Lento_2':'Lento 2'}
COLORS={'D':'#343a40','Paciente_1':'#2c7fb8','Paciente_2':'#00865a','Lento_1':'#d17a16','Lento_2':'#8b295f'}

def main():
    assert set(p.name for p in SERIES.glob('*.csv'))=={v[1] for v in DATASETS.values()}
    rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    plan=dict(date='2026-11-23',cases=CASES,parent_parameters={k:PARENTS[c['parent']] for k,c in CASES.items()},entry_parameters=ENTRY_PARAMETERS,rules=vars(rules),
              sources={k:dict(label=v[0],filename=v[1],sha256=hashlib.sha256((SERIES/v[1]).read_bytes()).hexdigest()) for k,v in DATASETS.items()},
              interpretation='Fixed configurations, no retuning. Exactly eight official CSVs in the specified directory, no reconstructed data. Some series already used in strategy development; not a wholly independent test set.',
              source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools').glob('*.py')},production_code_changed=False,fpga_programmed=False)
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib');os.environ['XDG_CACHE_HOME']='/private/tmp/ac4-ocho-series-cache'
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    money=FuncFormatter(lambda x,pos:f'{x:,.0f}'.replace(',','.'))
    summaries=[];validations=[]
    (ROOT/'graficos').mkdir(exist_ok=True)
    for dataset,(label,filename,prior_name) in DATASETS.items():
        prices=read_prices(SERIES/filename);assert len(prices)==20000
        folder=ROOT/'resultados'/dataset;folder.mkdir(parents=True,exist_ok=True);replays=[];curves={}
        for name in CASES:
            summary,rows,policy=simulate(prices,name);summary.update(dataset=dataset,series_label=label);summaries.append(summary)
            if prior_name:
                path=ROOT.parent/'2026-11-23_Baltazar_generaciones/resultados'/prior_name/(name+'.csv')
                prior=list(csv.DictReader(path.open()));keys=('price','applied_decision','next_decision','cash','shares','equity','orders','max_drawdown')
                assert len(prior)==len(rows) and all(all(int(a[k])==b[k] for k in keys) for a,b in zip(prior,rows)), 'Historical trace changed'
            write_csv(folder/(name+'.csv'),rows)
            if policy:(folder/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            curves[name]=[r['equity'] for r in rows];replays.append((dataset+'_'+name,rows))
        verify(replays,folder);validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
        fig,(ax,px)=plt.subplots(2,1,figsize=(11,4.6),sharex=True,gridspec_kw={'height_ratios':[3.5,1]})
        for name in CASES:
            ax.plot(curves[name],label=LABELS[name],color=COLORS[name],ls='--' if name.endswith('_1') else '-',lw=1.35)
        ax.axhline(10000,ls=':',lw=.8,color='#888888');ax.set_ylabel('Patrimonio');ax.yaxis.set_major_formatter(money);ax.grid(alpha=.15)
        ax.legend(ncol=5,fontsize=9,loc='upper left',bbox_to_anchor=(0,1.18),frameon=False)
        px.plot(prices,lw=.7,color='#657789');px.set(xlabel='Tick de mercado',ylabel='Precio');px.grid(alpha=.15)
        px.xaxis.set_major_formatter(money);fig.tight_layout(pad=.7,h_pad=.5)
        fig.savefig(ROOT/'graficos'/(dataset+'.png'),dpi=220);plt.close(fig)
        print(label,[(x['strategy'],x['equity']) for x in summaries if x['dataset']==dataset],flush=True)
    write_csv(ROOT/'resumen.csv',summaries)
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(x['compared_ticks'] for x in validations),datasets=8,runs=40,historical_trace_equivalence_runs=20,scope=validations[0]['scope']),indent=2))
    aggregates={}
    for name in CASES:
        group=[x for x in summaries if x['strategy']==name]
        aggregates[name]=dict(mean_equity=sum(x['equity'] for x in group)/8,min_equity=min(x['equity'] for x in group),max_equity=max(x['equity'] for x in group),
                              wins_vs_initial=sum(x['equity']>10000 for x in group),mean_commissions=sum(x['commissions'] for x in group)/8,
                              max_drawdown_percent=max(x['drawdown_percent'] for x in group))
    (ROOT/'agregados.json').write_text(json.dumps(aggregates,indent=2))

if __name__=='__main__':main()
