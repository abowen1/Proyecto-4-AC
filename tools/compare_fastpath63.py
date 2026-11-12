"""Archiva y compara D base de 84 instrucciones con la via rapida de 63."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil

from backtest import ROOT
from profile_d import analyze, csv_rows, write_csv

DEST = ROOT/'docs/informe/02_via_rapida_63_2026-11-12'
BASE_PROFILE = ROOT/'docs/informe/01_perfil_D_2026-11-12'
CASES = [
    ('practica_20000','perfil_D_20000','via63_20000','Práctica · 20.000'),
    ('ronda3_2000','perfil_D_2000_ronda3','via63_2000_ronda3','Ronda rápida · 2.000'),
    ('extremos','base84_extremos','via63_extremos','Extremos · 816'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(base, candidate, label):
    old=csv_rows(base/'metrics.csv');new=csv_rows(candidate/'metrics.csv')
    if len(old)!=len(new):raise ValueError('Longitudes diferentes')
    fields=('tick','price','next_decision','cash','shares')
    deltas=[]
    for a,b in zip(old,new):
        if any(a[k]!=b[k] for k in fields):raise ValueError(f'Diferencia funcional en {label}, tick {a["tick"]}')
        deltas.append(int(b['cycles'])-int(a['cycles']))
    old_cycles=sum(int(r['cycles']) for r in old)
    new_cycles=sum(int(r['cycles']) for r in new)
    old_max=max(int(r['cycles']) for r in old);new_max=max(int(r['cycles']) for r in new)
    result=dict(case=label,ticks=len(old),functional_parity=True,
                base_mean_cycles=old_cycles/len(old),new_mean_cycles=new_cycles/len(new),
                mean_speedup=old_cycles/new_cycles,time_reduction=1-new_cycles/old_cycles,
                base_max_cycles=old_max,new_max_cycles=new_max,max_speedup=old_max/new_max,
                faster_ticks=sum(d<0 for d in deltas),equal_ticks=sum(d==0 for d in deltas),slower_ticks=sum(d>0 for d in deltas),
                largest_regression_cycles=max(deltas),largest_saving_cycles=-min(deltas),
                base_total_ic=sum(int(r['instructions']) for r in old),new_total_ic=sum(int(r['instructions']) for r in new))
    write_csv(candidate/'diferencia_por_tick.csv',[dict(tick=a['tick'],base_cycles=int(a['cycles']),new_cycles=int(b['cycles']),delta_cycles=d) for a,b,d in zip(old,new,deltas)])
    return result


def draw(summary, old_profile, new_profile):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'ac4-fast63-v1','font.family':'DejaVu Sans'})
    def save(fig,name):
        svg=DEST/(name+'.svg');fig.savefig(svg,metadata={'Date':None})
        svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n')
        fig.savefig(DEST/(name+'.png'),dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,5.2),layout='constrained')
    x=np.arange(3); labels=[c[3] for c in CASES]
    for ax,field,title in zip(axes,['mean','max'],['Promedio','Máximo observado']):
        a=[r['base_'+field+'_cycles'] for r in summary];b=[r['new_'+field+'_cycles'] for r in summary]
        ax.bar(x-.19,a,.38,label='Base · 84 instrucciones',color='#999999')
        ax.bar(x+.19,b,.38,label='Vía rápida · 102 instrucciones',color='#0072b2')
        for i,(v,w) in enumerate(zip(a,b)):
            ax.text(i-.19,v+12,f'{v:.1f}' if field=='mean' else str(v),ha='center',fontsize=9)
            ax.text(i+.19,w+12,f'{w:.1f}' if field=='mean' else str(w),ha='center',fontsize=9)
        ax.set_xticks(x,labels,rotation=16);ax.set_title(title,loc='left');ax.set_ylabel('Ciclos de servicio')
        ax.set_ylim(0,max(a)*1.18);ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes[0].legend(loc='upper left',fontsize=9)
    fig.suptitle('D sin cambios bursátiles · Efecto medido del atajo de 63',fontsize=14)
    save(fig,'01_promedio_y_maximo')
    names={'io':'Recepción/publicación','contabilidad':'Contabilidad','ventana':'Ventana SMA32','senal':'Señal','cantidad_compra':'Cantidad de compra','cantidad_venta':'Cantidad de venta'}
    colors=['#999999','#2166ac','#009e73','#cc79a7','#d55e00','#e6ab02']
    fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained');left=[0.,0.]
    for old,new,color in zip(old_profile['major_sections'],new_profile['major_sections'],colors):
        values=[old['cycles_per_tick'],new['cycles_per_tick']]
        ax.barh(['Base de 84 instrucciones','Vía rápida de 63'],values,left=left,label=names[old['section']],color=color)
        left=[a+b for a,b in zip(left,values)]
    ax.set_xlabel('Ciclos promedio por precio · escala absoluta');ax.set_title('Qué costo se redujo · 20.000 precios',loc='left')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.19),ncol=3,frameon=False,fontsize=9);ax.spines[['top','right']].set_visible(False)
    save(fig,'02_perfil_comparado')
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
    x=np.arange(3);base=np.zeros(3)
    for key,label,color in [('faster_ticks','Más rápidos','#009e73'),('equal_ticks','Iguales','#999999'),('slower_ticks','Más lentos','#d55e00')]:
        values=[100*r[key]/r['ticks'] for r in summary]
        ax.barh(labels,values,left=base,label=label,color=color)
        for i,(v,l,r) in enumerate(zip(values,base,summary)):
            if v>5:ax.text(l+v/2,i,f"{v:.1f}%\n({r[key]})",ha='center',va='center',fontsize=9)
        base+=values
    ax.set_xlim(0,100);ax.set_xlabel('Porcentaje de precios');ax.set_title('Cambios por tick · Beneficios y regresiones de latencia',loc='left')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=3,frameon=False);ax.spines[['top','right']].set_visible(False)
    save(fig,'03_casos_rapidos_y_lentos')


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    summary=[]; profiles={}
    for case,base_run,new_run,label in CASES:
        base_source=BASE_PROFILE/case if case!='extremos' else ROOT/'build/strategy_d'/base_run
        new_source=ROOT/'build/strategy_d'/new_run
        for name,source in [('base',base_source),('optimizada',new_source)]:
            output=DEST/case/name;output.mkdir(parents=True,exist_ok=True)
            for f in ['metrics.csv','profile_ticks.csv','profile_pc.csv','pc_map.csv','profile_metadata.json','result.json']:
                shutil.copy2(source/f,output/f)
            report,_=analyze(output,output);profiles[(case,name)]=report
            log=ROOT/'build'/((base_run if name=='base' else new_run)+'.txt')
            if log.exists():shutil.copy2(log,output/'ejecucion.txt')
        summary.append(summarize(DEST/case/'base',DEST/case/'optimizada',case))
    # El cambio del banco para seleccionar imagen debe conservar la base anterior.
    previous=csv_rows(ROOT/'docs/evidencias/D_2026-11-12/extremos.csv')
    assert previous==csv_rows(DEST/'extremos/base/metrics.csv')
    old=profiles[('practica_20000','base')];new=profiles[('practica_20000','optimizada')]
    keys=('fill_buy_control','fill_buy_loop','size_buy_control','size_buy_loop')
    before=sum(d['cycles'] for d in old['detail'] if d['key'] in keys)
    after=sum(d['cycles'] for d in new['detail'] if d['key'] in keys)
    f=before/old['total_cycles'];local=before/after
    amdahl=dict(target_groups=keys,base_fraction=f,measured_local_speedup=local,
                predicted_global_speedup=1/(1-f+f/local),measured_global_speedup=old['total_cycles']/new['total_cycles'],
                explanation='Estimacion retrospectiva con aceleracion local medida, no prediccion independiente. Incluye costo de controles y atajos; se conserva tambien la prediccion previa en carpeta 01.')
    current=DEST/'practica_20000/optimizada'
    rows=csv_rows(current/'metrics.csv');stats={int(r['pc']):int(r['instructions']) for r in csv_rows(current/'profile_pc.csv')}
    instruction_counts={r['instruction']:stats.get(int(r['pc']),0) for r in csv_rows(current/'pc_map.csv')}
    expected_proposals=sum(int(r['next_decision'])==127 for r in rows)
    fills=[]
    for i,r in enumerate(rows):
        if i and int(rows[i-1]['next_decision'])==127:
            fills.append(int(r['shares'])-int(rows[i-1]['shares']))
    paths=dict(propose_fast_hits=instruction_counts['addi x9, x0, 127'],
               account_fast_hits=instruction_counts['sub x3, x11, x14'],
               expected_proposals_63=expected_proposals,expected_fills_63=sum(q==63 for q in fills),
               requested_63_but_filled_less=sum(q<63 for q in fills))
    assert paths['propose_fast_hits']==paths['expected_proposals_63']
    assert paths['account_fast_hits']==paths['expected_fills_63']
    write_csv(DEST/'comparacion.csv',summary)
    (DEST/'comparacion.json').write_text(json.dumps(dict(cases=summary,amdahl=amdahl,fast_path_coverage=paths),ensure_ascii=False,indent=2)+'\n')
    write_csv(DEST/'cambios_por_seccion.csv',[dict(section=a['section'],base_cycles_per_tick=a['cycles_per_tick'],new_cycles_per_tick=b['cycles_per_tick'],saved_cycles_per_tick=a['cycles_per_tick']-b['cycles_per_tick']) for a,b in zip(old['major_sections'],new['major_sections'])])
    for name,source in [('base','sw/trade_base_84'),('optimizada','sw/trade')]:
        p=DEST/'codigo'/name;p.mkdir(parents=True,exist_ok=True)
        for suffix in ('.s','.hex'):shutil.copy2(ROOT/(source+suffix),p/('trade'+suffix))
    files=['Makefile','sw/trade_base_84.s','sw/trade_base_84.hex','sw/trade.s','sw/trade.hex','tb/practica.csv','tb/tb_strategy_d.sv','tools/profile_d.py','tools/verify_strategy_d.py','tools/compare_fastpath63.py']
    files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'rtl').rglob('*.v'))]
    (DEST/'procedencia.json').write_text(json.dumps(dict(baseline_publication='d87656d7d8d92476eeac14da33a6cb6497a237e2',clock_hz=25000000,spi_hz=1000000,source_sha256={f:digest(ROOT/f) for f in files}),ensure_ascii=False,indent=2)+'\n')
    # Git y las herramientas de figuras usan finales LF.
    for p in DEST.rglob('*.csv'):p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    draw(summary,old,new)
    print(json.dumps(dict(cases=summary,amdahl=amdahl),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
