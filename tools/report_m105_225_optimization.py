"""Conserva mediciones, evidencia, Amdahl y figuras; no modifica la estrategia."""
import csv,gzip,hashlib,io,json,math,os,re,shutil,statistics
from pathlib import Path
from backtest import ROOT,read_prices
from measure_m105_225 import pc_map
from compare_m105_225_implementations import CASES

DEST=ROOT/'docs/estrategia/M105_225_optimizacion'
NAMES={'base':'Base funcional','soft':'Software optimizado','shifter':'A: shifter','qcap':'B: QCAP'}
COLORS=['#647789','#0072b2','#009e73','#cc6677']

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    DEST.mkdir(exist_ok=True);(DEST/'graficos').mkdir(exist_ok=True)
    data=json.loads((ROOT/'build/m105_225_measure/comparison.json').read_text());assert data['status']=='PASS'
    agg=data['aggregates'];results=data['results'];assert len(results)==312
    manifest=json.loads((ROOT/'build/final/M105_225.json').read_text());assert manifest['status']=='PASS' and not manifest['physical_programming']
    assert manifest['program_hex_sha256']==hashlib.sha256((ROOT/'sw/trade.hex').read_bytes()).hexdigest()
    stats=[];builds={}
    for case,a in agg.items():
        variant,program=CASES[case];path=ROOT/'build/hardware'/('M105_225_'+case)
        b=json.loads((path/'result.json').read_text());builds[case]=b
        image=ROOT/'build/m105_225_measure/compilers'/Path(program).stem/'program.hex'
        h=hashlib.sha256(image.read_bytes()).hexdigest()
        proofs=[r for r in results if r['case']==case];assert len(proofs)==78 and all(r['program_sha256']==h for r in proofs)
        assert h==hashlib.sha256((path/'program.hex').read_bytes()).hexdigest()
        text=(path/'synthesis.txt').read_text();lut=int(re.findall(r'^\s*(\d+)\s+SB_LUT4\s*$',text,re.M)[-1])
        a.update(lut4=lut,logic_cells=b['utilization']['ICESTORM_LC']['used'],bram=b['utilization']['ICESTORM_RAM']['used'],fmax_mhz=next(iter(b['fmax'].values()))['achieved'],program_sha256=h,
                 speedup_vs_base=agg['base']['mean_cycles']/a['mean_cycles'],time_reduction_vs_base=1-a['mean_cycles']/agg['base']['mean_cycles'])
        stats.append(dict(case=case,label=NAMES[case],**{k:v for k,v in a.items() if not isinstance(v,dict)}))
        folder=DEST/'compilacion'/case;folder.mkdir(parents=True,exist_ok=True)
        for f in ('result.json','assemble.txt','synthesis.txt','place_route.txt','program.hex'):shutil.copyfile(path/f,folder/f)
    write_csv(DEST/'comparacion.csv',stats)
    per_series=[]
    for r in results:
        per_series.append({k:r[k] for k in ('case','dataset','group','ticks','mean_cycles','max_cycles','mean_ic','max_ic','cpi','mean_us','max_us','program_sha256')})
    write_csv(DEST/'resultados_por_serie.csv',per_series)
    # Archive every measured tick of the8 official inputs,including explicit CPI/time.
    tick_folder=DEST/'mediciones_por_tick';tick_folder.mkdir(exist_ok=True)
    for r in results:
        if r['group']!='catedra':continue
        source=ROOT/'build/m105_225/runs'/('profile_'+Path(r['program']).stem+'_'+r['dataset'])/'actual.csv'
        with source.open() as f:raw=list(csv.DictReader(f))
        target=tick_folder/(r['case']+'_'+r['dataset']+'.csv.gz')
        with target.open('wb') as binary:
            with gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed:
                with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as text:
                    fields=list(raw[0])+['cpi_service','execution_ns']
                    w=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');w.writeheader()
                    for row in raw:row.update(cpi_service=int(row['cycles'])/int(row['instructions']),execution_ns=int(row['cycles'])*40);w.writerow(row)
    # Independent algorithm-reference comparison,matching the master's baseline formula.
    references=[]
    for r in results:
        if r['case']!='soft':continue
        prices=read_prices(ROOT/'build/m105_225/inputs'/(r['dataset']+'.csv'))
        q=(10000-5)//prices[0];cash=10000-5-q*prices[0];peak=10000;dd=0
        for p in prices:wealth=cash+q*p;peak=max(peak,wealth);dd=max(dd,peak-wealth)
        references.append(dict(dataset=r['dataset'],M105_225_final=r['summary']['equity'],M105_225_orders=r['summary']['orders'],M105_225_commissions=r['summary']['commissions'],M105_225_max_dd=r['summary']['max_drawdown'],no_operar=10000,comprar_mantener=cash+q*prices[-1],comprar_mantener_orders=1,comprar_mantener_commissions=5,comprar_mantener_max_dd=dd))
    write_csv(DEST/'referencias_financieras.csv',references)
    refstats={
      'M105-225':dict(mean=statistics.mean(r['M105_225_final'] for r in references),minimum=min(r['M105_225_final'] for r in references),mean_orders=statistics.mean(r['M105_225_orders'] for r in references),mean_commissions=statistics.mean(r['M105_225_commissions'] for r in references),max_dd=max(r['M105_225_max_dd'] for r in references)),
      'No operar':dict(mean=10000,minimum=10000,mean_orders=0,mean_commissions=0,max_dd=0),
      'Comprar y mantener (maestra)':dict(mean=statistics.mean(r['comprar_mantener'] for r in references),minimum=min(r['comprar_mantener'] for r in references),mean_orders=1,mean_commissions=5,max_dd=max(r['comprar_mantener_max_dd'] for r in references))}
    # Disjoint PC intervals for the only accelerated hardware kernel: bounded quantity.
    kernel={}
    for case in ('soft','shifter','qcap'):
        labels,_=pc_map(ROOT/CASES[case][1]);start_f=labels['fill_buy']+8;end_f=labels.get('fill_quantity_done',start_f+4)
        start_s=labels['size_buy']+4;end_s=labels.get('size_quantity_done',start_s+4)
        details=[p for r in results if r['case']==case for p in r['pc_details']]
        pcs=[p for p in details if start_f<=p['pc']<end_f or start_s<=p['pc']<end_s]
        cycles=sum(p['cycles'] for p in pcs);ic=sum(p['instructions'] for p in pcs)
        calls=sum(p['instructions'] for p in details if p['pc'] in (start_f,start_s))
        kernel[case]=dict(cycles=cycles,instructions=ic,queries=calls,ops_per_second=calls*25000000/cycles,
                          data_ram_bytes=0,intensity_data_only='infinity',ideal_issue_roof_ops_s=12500000/(ic/calls),
                          model='Useful op=one bounded quantity query. No data-RAM accesses in this register-only kernel. Ideal issue ceiling is12.5M retired RV instructions/s divided by measured IC/query; not a measured sustainable peak.')
    assert len({v['queries'] for v in kernel.values()})==1
    policy_pcs=[p for r in results if r['case']=='soft' for p in r['pc_details'] if p['section']=='policy']
    policy_cycles=sum(p['cycles'] for p in policy_pcs);policy_ic=sum(p['instructions'] for p in policy_pcs)
    policy_kernel=dict(cycles=policy_cycles,instructions=policy_ic,operations=agg['soft']['ticks'],ops_per_second=agg['soft']['ticks']*25000000/policy_cycles,data_ram_bytes=0,intensity_data_only='infinity',ideal_issue_roof_ops_s=12500000/(policy_ic/agg['soft']['ticks']),definition='One policy evaluation per input tick; excludes IO,accounting and quantity kernel.')
    amdahl=[]
    targets=['policy','buy_account','sell_account','size_buy']
    before=sum(agg['base']['sections'][s] for s in targets);after=sum(agg['soft']['sections'][s] for s in targets)
    for name,bef,aft,total,actual in [('software',before,after,agg['base']['total_cycles'],agg['base']['mean_cycles']/agg['soft']['mean_cycles']),*[(c,kernel['soft']['cycles'],kernel[c]['cycles'],agg['soft']['total_cycles'],agg['soft']['mean_cycles']/agg[c]['mean_cycles']) for c in ('shifter','qcap')]]:
        f=bef/total
        for speed in (2,4,10,math.inf):amdahl.append(dict(target=name,fraction=f,local_speedup='infinity' if math.isinf(speed) else speed,predicted_speedup=1/(1-f+f/speed),kind='hypothetical',measured_global_speedup=actual))
        amdahl.append(dict(target=name,fraction=f,local_speedup=bef/aft,predicted_speedup=1/(1-f+f/(bef/aft)),kind='retrospective_using_measured_local_cost',measured_global_speedup=actual))
    write_csv(DEST/'amdahl.csv',amdahl);write_csv(DEST/'roofline.csv',[dict(case=k,**v) for k,v in kernel.items()])
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/ac4-M-mpl')
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    import numpy as np
    def save(fig,name):fig.tight_layout();fig.savefig(DEST/'graficos'/(name+'.png'),dpi=170);plt.close(fig)
    labels=[NAMES[c] for c in agg]
    fig,axes=plt.subplots(1,2,figsize=(11.5,4))
    for ax,key,title in [(axes[0],'mean_cycles','Media de servicio'),(axes[1],'max_cycles','Mayor latencia observada')]:
        values=[agg[c][key] for c in agg];bars=ax.bar(labels,values,color=COLORS)
        for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,b.get_height(),f'{v:.3f}' if key=='mean_cycles' else str(v),ha='center',va='bottom',fontsize=8)
        ax.set(title=title,ylabel='Ciclos a25MHz',ylim=(0,max(values)*1.18));ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.15)
    save(fig,'01_ciclos')
    sections=agg['base']['sections'];names={'io':'Recepción/publicación','account_control':'Despacho contable','policy':'Despacho de estados','buy_account':'Contabilizar compra','sell_account':'Contabilizar venta','size_buy':'Dimensionar compra','sell_quantity':'Cantidad de venta'}
    fig,ax=plt.subplots(figsize=(11.5,4));keys=sorted(sections,key=sections.get);values=[100*sections[k]/agg['base']['total_cycles'] for k in keys]
    bars=ax.barh([names[k] for k in keys],values,color='#0072b2')
    for b,v in zip(bars,values):ax.text(v+.3,b.get_y()+b.get_height()/2,f'{v:.3f} %',va='center',fontsize=9)
    ax.set(xlabel='Porcentaje del tiempo de respuesta base',xlim=(0,53),title='Perfil de M105-225 base; espera ociosa excluida');save(fig,'02_perfil')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4));x=np.linspace(1,20,150)
    for ax,targets_plot in [(axes[0],['software']),(axes[1],['shifter','qcap'])]:
        for name in targets_plot:
            r=next(a for a in amdahl if a['target']==name);f=r['fraction'];ax.plot(x,1/(1-f+f/x),label=name+f' | f={f:.5%}')
            rr=next(a for a in amdahl if a['target']==name and a['kind'].startswith('retrospective'));ax.scatter([rr['local_speedup']],[rr['measured_global_speedup']],s=25)
        ax.set(xlabel='Aceleración local hipotética',ylabel='Aceleración global',title='Amdahl; punto=medición');ax.legend(fontsize=7);ax.grid(alpha=.2)
    save(fig,'03_amdahl')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4))
    for ax,key,title in [(axes[0],'lut4','LUT4 utilizadas'),(axes[1],'fmax_mhz','Fmax estimada por timing')]:
        values=[agg[c][key] for c in agg];bars=ax.bar(labels,values,color=COLORS)
        for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v,f'{v:.2f}',ha='center',va='bottom',fontsize=8)
        ax.set(title=title,ylim=(0,max(values)*1.18));ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.15)
    axes[1].axhline(25,color='black',ls=':',label='Reloj implementado25MHz');axes[1].legend(fontsize=8);save(fig,'04_recursos')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4));intensity=np.logspace(-5,3,200)
    ax=axes[0];k=policy_kernel
    ax.loglog(intensity,np.minimum(100000000*intensity,k['ideal_issue_roof_ops_s']),color=COLORS[1],label='Techo ideal normalizado')
    ax.scatter([1000],[k['ops_per_second']],color=COLORS[1],s=40)
    ax.annotate(f"{k['ops_per_second']:,.0f} evaluaciones/s",(1000,k['ops_per_second']),xytext=(-160,-18),textcoords='offset points',fontsize=7)
    ax.set(title='Kernel principal: política por precio',xlabel='Evaluaciones/byte (posición simbólica: infinito)',ylabel='Evaluaciones de política por segundo')
    ax.legend(fontsize=7);ax.grid(alpha=.2,which='both')
    ax=axes[1]
    for case,color in zip(('soft','shifter','qcap'),COLORS[1:]):
        k=kernel[case];roof=k['ideal_issue_roof_ops_s'];ax.loglog(intensity,np.minimum(100000000*intensity,roof),color=color,label=NAMES[case])
        ax.scatter([1000],[k['ops_per_second']],color=color,s=30);ax.annotate(f"{case}: {k['ops_per_second']:,.0f}/s",(1000,k['ops_per_second']),xytext=(-135,-12),textcoords='offset points',color=color,fontsize=6.5)
    ax.set(xlabel='Consultas/byte (posición simbólica: infinito)',ylabel='Consultas de cantidad por segundo',title='Kernel aritmético: cantidad acotada')
    ax.legend(loc='upper left',fontsize=6.5);ax.grid(alpha=.2,which='both');save(fig,'05_roofline')
    # Preserve tools,actual evidence,and the selected bitstream.
    for source,target in [(ROOT/'build/m105_225_measure/stress.json',DEST/'stress.json'),(ROOT/'build/m105_225_measure/integration/soft/result.json',DEST/'integracion_final.json'),(ROOT/'build/canvas_m105_225_variants/software/trade/practica_meta/2000_100000_iverilog/result.json',DEST/'canvas_final.json')]:shutil.copyfile(source,target)
    (DEST/'imagen').mkdir(exist_ok=True);shutil.copyfile(ROOT/'build/final/M105_225.bin',DEST/'imagen/M105_225.bin');shutil.copyfile(ROOT/'build/final/M105_225.json',DEST/'imagen/manifest.json')
    proofs=[dict(case=r['case'],dataset=r['dataset'],ticks=r['ticks'],program_sha256=r['program_sha256'],status='PASS') for r in results]
    (DEST/'validacion_variantes.json').write_text(json.dumps(dict(status='PASS',results=proofs,series_per_case=78,profile_baselines_reused=sum(r.get('profile_reused',False) for r in results)),indent=2))
    report=dict(status='PASS',strategy='M105-225',chosen='soft',clock_hz=25000000,aggregates=agg,kernel=kernel,policy_kernel=policy_kernel,amdahl=amdahl,financial_references=refstats,
                selected_mean_time_reduction=1-agg['soft']['mean_cycles']/agg['base']['mean_cycles'],selected_worst_time_reduction=1-agg['soft']['max_cycles']/agg['base']['max_cycles'],
                official_tick_traces=32,full_profiles=312,full_profile_ticks=6240000,hardware_alternatives=['shifter','qcap'],physical_programming=False,physical_validation=False,
                final_image=manifest,deadline_fastest_round_cycles=2262,deadline_margin_cycles=2262-agg['soft']['max_cycles'])
    (DEST/'resumen.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:agg[k]['mean_cycles'] for k in agg}),flush=True)

if __name__=='__main__':main()
