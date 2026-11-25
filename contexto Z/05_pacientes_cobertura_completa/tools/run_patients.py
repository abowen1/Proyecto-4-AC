"""Solo Paciente1/2: entradas únicas de cátedra y 70 bloques recreados existentes."""
import csv,hashlib,json,os,math
from collections import defaultdict
from pathlib import Path
from backtest import ROOT,official_rules,read_prices,write_csv
from generations import CASES,ENTRY_PARAMETERS
from baltazar import CASES as PARENTS
from compare_generations import simulate
from verify_market import verify

TOTAL=ROOT.parents[1];CANVAS=TOTAL/'Material de Canvas AC4';RECREATED=TOTAL/'series recreadas'
NAMES={'Paciente_1':'Paciente 1','Paciente_2':'Paciente 2'}
COLORS={'Paciente_1':'#2c7fb8','Paciente_2':'#00865a'}
SYMBOL_NAMES={'META':'Meta','AAPL':'Apple','NFLX':'Netflix','AMD':'AMD','TSLA':'Tesla'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def inventory():
    sources=[];seen={};duplicates=[]
    labels={'practica_meta_2022':'Meta 2022','practica_amd_2022_ene':'AMD 2022 - enero','practica_amd_2022_may':'AMD 2022 - mayo',
            'practica_tesla_2022':'Tesla 2022','practica_apple_2022':'Apple 2022','practica_apple_2023':'Apple 2023',
            'practica_netflix_2022':'Netflix 2022','practica_netflix_2023':'Netflix 2023'}
    official=sorted((CANVAS/'Proyecto 4 Series Practica').glob('*.csv'))
    assert len(official)==8
    for p in official+[CANVAS/'practica_meta.csv',CANVAS/'practica.csv']:
        digest=sha(p)
        if digest in seen:duplicates.append(dict(path=str(p),same_as=seen[digest],sha256=digest));continue
        sid='C_'+p.stem;seen[digest]=sid
        sources.append(dict(id=sid,path=str(p),filename=p.name,sha256=digest,label=labels.get(p.stem,'Práctica original anterior'),
                            group='original' if p.name=='practica.csv' else 'catedra',symbol=next((s for s,k in [('AMD','amd'),('AAPL','apple'),('META','meta'),('NFLX','netflix'),('TSLA','tesla')] if k in p.stem),'ORIGINAL')))
    meta=json.loads((RECREATED/'indice_series.json').read_text());assert meta['series_count']==70
    assert {str(p.relative_to(RECREATED)) for p in RECREATED.rglob('*.csv')}=={r['file'] for r in meta['series']}
    for row in sorted(meta['series'],key=lambda r:(r['symbol'],r['number'])):
        p=RECREATED/row['file'];digest=sha(p);assert digest==row['sha256']
        if digest in seen:duplicates.append(dict(path=str(p),same_as=seen[digest],sha256=digest));continue
        sid=f"R_{row['symbol']}_{row['number']:02d}";seen[digest]=sid
        sources.append(dict(id=sid,path=str(p),filename=p.name,sha256=digest,group='recreada',symbol=row['symbol'],
                            label=f"{SYMBOL_NAMES[row['symbol']]} - bloque {row['number']:02d}",start_ny=row['start_ny'],end_ny=row['end_ny']))
    assert len(sources)==79 and len(duplicates)==1
    return sources,duplicates

def main():
    sources,duplicates=inventory();rules=official_rules();assert vars(rules)==dict(cash=10000,commission=5)
    plan=dict(date='2026-11-23',strategies={n:dict(case=CASES[n],parameters=PARENTS[CASES[n]['parent']]) for n in NAMES},entry_parameters=ENTRY_PARAMETERS,
              rules=vars(rules),sources=sources,duplicates_excluded=duplicates,
              averaging='Arithmetic mean at same relative tick over all79 unique series, equal weight1/79, each restarts at10000. Not chronological portfolio; groups also reported.',
              scope='8 real-market official series +1 older original practice +70 recreated blocks. Official and recreated periods can overlap. Not79 independent samples. No parameter tuning.',
              production_code_changed=False,fpga_programmed=False,
              source_sha256={p.name:sha(p) for p in (ROOT/'tools').glob('*.py')})
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    os.environ['MPLCONFIGDIR']=str(ROOT/'cache_matplotlib');os.environ['XDG_CACHE_HOME']='/private/tmp/ac4-pacientes-cache'
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    money=FuncFormatter(lambda x,pos:f'{x:,.0f}'.replace(',','.'))
    (ROOT/'graficos').mkdir(exist_ok=True)
    summaries=[];validations=[];sums=defaultdict(lambda:{n:[0]*20000 for n in NAMES});counts=defaultdict(int)
    prior_root=ROOT.parent/'2026-11-23_Baltazar_ocho_series'
    prior_plan=json.loads((prior_root/'plan.json').read_text());prior_by_hash={r['sha256']:sid for sid,r in prior_plan['sources'].items()};historical=0
    for number,s in enumerate(sources,1):
        prices=read_prices(Path(s['path']));assert len(prices)==20000
        folder=ROOT/'resultados'/s['id'];folder.mkdir(parents=True,exist_ok=True);replays=[];curves={}
        groups=['global',s['group']]
        if s['group']=='recreada':groups.append('recreada_'+s['symbol'])
        for g in groups:counts[g]+=1
        for name in NAMES:
            result,rows,policy=simulate(prices,name);result.update(dataset=s['id'],series_label=s['label'],group=s['group'],symbol=s['symbol']);summaries.append(result)
            if s['sha256'] in prior_by_hash:
                old=list(csv.DictReader((prior_root/'resultados'/prior_by_hash[s['sha256']]/(name+'.csv')).open()))
                keys=('price','applied_decision','next_decision','cash','shares','equity','orders','max_drawdown')
                assert len(old)==len(rows) and all(all(int(a[k])==b[k] for k in keys) for a,b in zip(old,rows));historical+=1
            write_csv(folder/(name+'.csv'),rows)
            (folder/(name+'_operaciones.json')).write_text(json.dumps(policy.closed,indent=2))
            curves[name]=[r['equity'] for r in rows]
            for g in groups:
                for i,value in enumerate(curves[name]):sums[g][name][i]+=value
            replays.append((s['id']+'_'+name,rows))
        verify(replays,folder);validations.append(json.loads((folder/'validacion_contabilidad.json').read_text()))
        fig,(ax,px)=plt.subplots(2,1,figsize=(11,4.9),sharex=True,gridspec_kw={'height_ratios':[4,1]})
        for name in NAMES:ax.plot(curves[name],label=NAMES[name],color=COLORS[name],lw=1.45)
        ax.axhline(10000,color='#999999',ls=':',lw=.7);ax.set_ylabel('Patrimonio');ax.yaxis.set_major_formatter(money);ax.legend(loc='upper left',ncol=2,frameon=False);ax.grid(alpha=.15)
        px.plot(prices,color='#657789',lw=.7);px.set(xlabel='Tick de mercado',ylabel='Precio');px.xaxis.set_major_formatter(money);px.grid(alpha=.15)
        fig.tight_layout(pad=.6,h_pad=.4);fig.savefig(ROOT/'graficos'/(s['id']+'.png'),dpi=170);plt.close(fig)
        print(f"{number}/{len(sources)} {s['label']} | "+' | '.join(n+':'+str(next(x['equity'] for x in summaries if x['dataset']==s['id'] and x['strategy']==n)) for n in NAMES),flush=True)
    write_csv(ROOT/'resumen.csv',summaries)
    means={g:{n:[x/counts[g] for x in values] for n,values in by_name.items()} for g,by_name in sums.items()}
    write_csv(ROOT/'patrimonio_promedio.csv',[dict(tick=i,**{g+'_'+n:means[g][n][i] for g in means for n in NAMES}) for i in range(20000)])
    groups={}
    for g,count in counts.items():
        subset=[s['id'] for s in sources if g=='global' or s['group']==g or (g.startswith('recreada_') and s['group']=='recreada' and s['symbol']==g.split('_',1)[1])]
        stats={}
        for n in NAMES:
            rr=[r for r in summaries if r['strategy']==n and r['dataset'] in subset]
            assert len(rr)==count
            stats[n]=dict(mean_equity=math.fsum(r['equity'] for r in rr)/count,min_equity=min(r['equity'] for r in rr),mean_commissions=math.fsum(r['commissions'] for r in rr)/count,
                          wins_vs_initial=sum(r['equity']>10000 for r in rr),max_drawdown_percent=max(r['drawdown_percent'] for r in rr),
                          series_wins=sum(r['equity']>next(x['equity'] for x in summaries if x['dataset']==r['dataset'] and x['strategy']!=n) for r in rr))
            assert means[g][n][0]==10000 and abs(means[g][n][-1]-stats[n]['mean_equity'])<1e-8
        groups[g]=dict(count=count,strategies=stats)
    (ROOT/'agregados.json').write_text(json.dumps(groups,indent=2))
    (ROOT/'validacion_contabilidad.json').write_text(json.dumps(dict(status='PASS',compared_ticks=sum(x['compared_ticks'] for x in validations),series=len(sources),runs=len(summaries),historical_trace_equivalence_runs=historical,scope=validations[0]['scope']),indent=2))
    # Esta imagen será el último gráfico del PDF, después de todos los casos.
    fig,ax=plt.subplots(figsize=(11,5.1))
    for n in NAMES:ax.plot(means['global'][n],label=NAMES[n],color=COLORS[n],lw=2)
    ax.axhline(10000,color='#999999',ls=':',lw=.8);ax.set(xlabel='Tick relativo de cada corrida',ylabel='Patrimonio promedio')
    ax.xaxis.set_major_formatter(money);ax.yaxis.set_major_formatter(money);ax.legend(frameon=False);ax.grid(alpha=.15)
    fig.tight_layout();fig.savefig(ROOT/'graficos/promedio_global.png',dpi=220);plt.close(fig)
    print('FIN:158 corridas,79 series, promedio verificado y parámetros sin cambios',flush=True)

if __name__=='__main__':main()
