"""Comparacion reproducible de software, shifter acotado y QCAP a 25 MHz."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil

from hardware_variants import ROOT, VARIANTS, rtl_sources
from profile_d import analyze, csv_rows, write_csv

DEST=ROOT/'docs/informe/03_hardware_2026-11-12'
SOFTWARE=ROOT/'docs/informe/02_via_rapida_63_2026-11-12'
CASES={'practica_20000':'20000','ronda3_2000':'2000_ronda3','extremos':'extremos'}
LABELS={'software':'Software 102','shifter':'A · Shifter acotado','qcap':'B · QCAP'}
TARGETS={
    'shifter':('fill_buy_control','fill_buy_loop','fill_sell_control','fill_sell_loop','times32','size_buy_control','size_buy_loop'),
    'qcap':('size_buy_control','size_buy_loop'),
}


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def archive():
    records=[];profiles={};builds={}
    for variant in VARIANTS:
        hw=ROOT/'build/hardware'/variant
        builds[variant]=json.loads((hw/'result.json').read_text())
        out=DEST/'compilacion'/variant;out.mkdir(parents=True,exist_ok=True)
        for f in ('assemble.txt','synthesis.txt','place_route.txt','result.json','program.hex'):
            shutil.copy2(hw/f,out/f)
        build_meta=builds[variant]
        build_meta['image_sha256']=digest(hw/'soc.bin')
        (out/'imagen.json').write_text(json.dumps(build_meta,indent=2)+'\n')
        for case,suffix in CASES.items():
            source=ROOT/'build/strategy_d'/f'hw_{variant}_{suffix}_por63'
            dest=DEST/'mediciones'/case/variant;dest.mkdir(parents=True,exist_ok=True)
            for f in ('metrics.csv','profile_ticks.csv','profile_pc.csv','pc_map.csv','profile_metadata.json','result.json'):
                shutil.copy2(source/f,dest/f)
            log=ROOT/'build'/f'hw_{variant}_{suffix}_por63.txt'
            if log.exists():shutil.copy2(log,dest/'ejecucion.txt')
            profile,_=analyze(dest,dest);profiles[(case,variant)]=profile
            rows=csv_rows(dest/'metrics.csv')
            base=csv_rows(SOFTWARE/case/'optimizada/metrics.csv')
            if len(base)!=len(rows):raise ValueError('Serie incompleta')
            for a,b in zip(base,rows):
                if any(a[k]!=b[k] for k in ('tick','price','next_decision','cash','shares')):
                    raise ValueError(f'Diferencia funcional {variant}/{case}, tick {a["tick"]}')
            result=json.loads((dest/'result.json').read_text())
            oldpath=ROOT/'build/strategy_d'/f'hw_software_{suffix}_por63'
            old=json.loads((oldpath/'result.json').read_text())['metrics']
            oldrows=csv_rows(oldpath/'metrics.csv')
            delta=[int(b['cycles'])-int(a['cycles']) for a,b in zip(oldrows,rows)]
            r=dict(case=case,variant=variant,ticks=len(rows),functional_parity=True,
                mean_cycles=profile['mean_cycles'],max_cycles=int(profile['worst_tick']['cycles']),
                mean_ic=profile['total_instructions']/len(rows),cpi=profile['cpi'],
                mean_us=profile['mean_cycles']*.04,max_us=int(profile['worst_tick']['cycles'])*.04,
                speedup=old['mean_cycles']/profile['mean_cycles'],time_reduction=1-profile['mean_cycles']/old['mean_cycles'],
                service_decisions_per_second=25000000/profile['mean_cycles'],
                logic_cells=build_meta['utilization']['ICESTORM_LC']['used'],bram=build_meta['utilization']['ICESTORM_RAM']['used'],
                fmax_mhz=next(iter(build_meta['fmax'].values()))['achieved'],
                faster_ticks=sum(d<0 for d in delta),equal_ticks=sum(d==0 for d in delta),slower_ticks=sum(d>0 for d in delta),
                max_regression_cycles=max(0,max(delta)),static_words=len((hw/'program.hex').read_text().split()),
                final_equity=result['expected_summary']['equity'],orders=result['expected_summary']['orders'])
            records.append(r)
    write_csv(DEST/'comparacion.csv',records)
    amdahl=[]
    base=profiles[('practica_20000','software')]
    for variant,keys in TARGETS.items():
        measured=profiles[('practica_20000',variant)]
        before=sum(d['cycles'] for d in base['detail'] if d['key'] in keys)
        after=sum(d['cycles'] for d in measured['detail'] if d['key'] in keys)
        f=before/base['total_cycles']
        for local in (2,4,10,math.inf):
            amdahl.append(dict(variant=variant,local_speedup='infinito' if math.isinf(local) else local,
                               fraction=f,predicted_global_speedup=1/(1-f+f/local),kind='escenario hipotetico con f de software'))
        local=before/after
        amdahl.append(dict(variant=variant,local_speedup=local,fraction=f,
                           predicted_global_speedup=1/(1-f+f/local),kind='reconstruccion retrospectiva usando costo local medido'))
    write_csv(DEST/'amdahl.csv',amdahl)
    roof=[]
    for variant in VARIANTS:
        profile=profiles[('practica_20000',variant)]
        pc=csv_rows(DEST/'mediciones/practica_20000'/variant/'instrucciones.csv')
        counts={r['instruction']:int(r['instructions']) for r in pc}
        operations=counts['add x6, x6, x5']+counts['sub x6, x6, x10']
        data_bytes=4*(counts['lw x10, 0(x11)']+counts['sw x5, 0(x11)'])
        cycles=next(d['cycles'] for d in profile['detail'] if d['key']=='window')
        roof.append(dict(variant=variant,kernel='actualizacion ventana SMA32',useful_add_sub=operations,
            data_port_bytes=data_bytes,intensity_ops_per_byte=operations/data_bytes,service_cycles=cycles,
            measured_integer_ops_per_second=operations*25000000/cycles,
            arithmetic_peak_ops_per_second=12500000,data_port_peak_bytes_per_second=100000000,
            ideal_roof_ops_per_second=min(12500000,100000000*operations/data_bytes)))
    write_csv(DEST/'roofline.csv',roof)
    report=dict(records=records,amdahl=amdahl,roofline=roof,recommended_variant='shifter',startup_reset_clocks=63,
                physical_selftests_reference='placa.json',
                same_clock_hz=25000000,physical_spi_validated=False)
    (DEST/'comparacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    files=[ROOT/'Makefile',ROOT/'tools/assembler.py',ROOT/'tools/verify_strategy_d.py',ROOT/'tools/profile_d.py',ROOT/'tools/hardware_variants.py',ROOT/'tools/test_hardware.py',ROOT/'tools/compare_hardware.py']
    files+=sorted((ROOT/'tb').glob('tb_*unit.sv'))+[ROOT/'tb/tb_hw_instructions.sv',ROOT/'tb/tb_strategy_d.sv',ROOT/'tb/tb_hw_gate.sv',ROOT/'tb/tb_trace_uart.sv',ROOT/'tools/read_trace_uart.py']
    files+=sorted((ROOT/'tests').glob('test_hardware*.py'))
    files+=sorted((ROOT/'variants').rglob('*.v'))
    files+=sorted((ROOT/'rtl').rglob('*.v'))
    files+=[ROOT/v['program'] for v in VARIANTS.values()]+[ROOT/'sw/qcap_diagnostic.s',ROOT/'sw/shifter_diagnostic.s',ROOT/'sw/shifter_probe.s',ROOT/'sw/shifter_stress.s',ROOT/'tb/practica.csv']
    (DEST/'procedencia.json').write_text(json.dumps(dict(baseline_commit='e15c74065b9dec7fee5be7340055f6a3f4066db6',source_sha256={str(p.relative_to(ROOT)):digest(p) for p in files}),ensure_ascii=False,indent=2)+'\n')
    tests=DEST/'pruebas';tests.mkdir(exist_ok=True)
    for f in (ROOT/'build/hardware/tests').glob('*.txt'):shutil.copy2(f,tests/f.name)
    for p in DEST.rglob('*.csv'):p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    for p in DEST.rglob('*.txt'):p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
    return report


def figures(report):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'ac4-hardware-v1','font.family':'DejaVu Sans'})
    def save(fig,name):
        svg=DEST/(name+'.svg');fig.savefig(svg,metadata={'Date':None})
        svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n')
        fig.savefig(DEST/(name+'.png'),dpi=180);plt.close(fig)
    full=[r for r in report['records'] if r['case']=='practica_20000']
    fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    colors=['#999999','#0072b2','#d55e00']
    for ax,field,title in zip(axs,['mean_cycles','max_cycles'],['Promedio','Máximo observado']):
        bars=ax.bar([LABELS[r['variant']] for r in full],[r[field] for r in full],color=colors)
        for b,r in zip(bars,full):ax.text(b.get_x()+b.get_width()/2,b.get_height()+max(v[field] for v in full)*.025,f"{r[field]:.2f}" if field=='mean_cycles' else str(r[field]),ha='center')
        ax.set_ylim(0,max(v[field] for v in full)*1.15);ax.set_ylabel('Ciclos de servicio');ax.set_title(title,loc='left');ax.tick_params(axis='x',rotation=12);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('D · 20.000 precios · Tres implementaciones a 25 MHz');save(fig,'01_tiempos')
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    for r,color in zip(full,colors):
        ax.scatter(r['logic_cells'],r['mean_us'],s=110,color=color,label=f"{LABELS[r['variant']]} · {r['logic_cells']} celdas")
        ax.annotate(f"{r['mean_us']:.3f} us",(r['logic_cells'],r['mean_us']),xytext=(5,10),textcoords='offset points')
    ax.axvline(1280,color='#555555',ls=':',label='Capacidad HX1K: 1.280');ax.set_xlim(1050,1300)
    ax.set_xlabel('Celdas lógicas utilizadas');ax.set_ylabel('Tiempo promedio de servicio (us)')
    ax.set_title('Costo de área frente a latencia · menor altura es mejor',loc='left');ax.grid(alpha=.2);ax.legend(loc='lower left');ax.spines[['top','right']].set_visible(False);save(fig,'02_area_y_latencia')
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained');x=np.geomspace(.005,10,300)
    ax.loglog(x,np.minimum(12.5,100*x),color='#555555',lw=2,label='Techo ideal: 12,5 Mops/s y 100 MB/s')
    r=report['roofline'][0]
    ax.scatter(r['intensity_ops_per_byte'],r['measured_integer_ops_per_second']/1e6,s=110,color='#0072b2',zorder=5)
    ax.annotate('SMA32 · las tres variantes coinciden\n0,25 op/B · 2,082 Mops/s',(r['intensity_ops_per_byte'],r['measured_integer_ops_per_second']/1e6),xytext=(14,-36),textcoords='offset points',fontsize=10)
    ax.set_xlabel('Intensidad aritmética del kernel (sumas/restas útiles por byte de datos)');ax.set_ylabel('Millones de sumas/restas útiles por segundo')
    ax.set_title('Roofline del kernel común SMA32 a 25 MHz',loc='left');ax.grid(which='both',alpha=.15);ax.legend(loc='upper left');save(fig,'03_roofline_sma32')
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained');x=np.linspace(1,15,200)
    for variant,color in [('shifter','#0072b2'),('qcap','#d55e00')]:
        r=next(r for r in report['amdahl'] if r['variant']==variant);f=r['fraction']
        ax.plot(x,1/(1-f+f/x),color=color,label=f"{LABELS[variant]} · región f={f:.1%}")
        ax.axhline(1/(1-f),color=color,ls=':',lw=.8)
        retrospective=next(r for r in report['amdahl'] if r['variant']==variant and r['kind'].startswith('reconstruccion'))
        measured=next(r for r in full if r['variant']==variant)
        ax.scatter(retrospective['local_speedup'],measured['speedup'],color=color,s=65,zorder=5)
    ax.set_xlabel('Aceleración local de la región modificada');ax.set_ylabel('Aceleración total del servicio')
    ax.set_title('Amdahl · curvas hipotéticas y puntos con costo local medido',loc='left');ax.grid(alpha=.2);ax.legend();ax.spines[['top','right']].set_visible(False);save(fig,'04_amdahl')


if __name__=='__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    report=archive();figures(report)
    print(json.dumps([r for r in report['records'] if r['case']=='practica_20000'],ensure_ascii=False,indent=2))
