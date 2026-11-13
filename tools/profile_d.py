"""Mapa de PC y analisis reproducible del perfil pasivo de D."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

from assembler import assemble
from backtest import ROOT

GROUPS = [
    ('io', 'Recepción y publicación', 'io'),
    ('account_control', 'Despacho contable', 'contabilidad'),
    ('fill_buy_control', 'Compra ejecutada: control', 'contabilidad'),
    ('fill_buy_loop', 'Compra ejecutada: bucle', 'contabilidad'),
    ('fill_sell_control', 'Venta ejecutada: control', 'contabilidad'),
    ('fill_sell_loop', 'Venta ejecutada: bucle', 'contabilidad'),
    ('window', 'Actualizar ventana de 32', 'ventana'),
    ('times32', 'Calcular 32 × precio', 'senal'),
    ('signal', 'Comparar señal', 'senal'),
    ('size_buy_control', 'Nueva compra: control', 'cantidad_compra'),
    ('size_buy_loop', 'Nueva compra: bucle', 'cantidad_compra'),
    ('size_sell', 'Nueva venta: cantidad', 'cantidad_venta'),
]


def prepare_profile(output, program=None, program_hex=None, isa='base'):
    program = program or ROOT / 'sw/trade.s'
    source = program.read_text()
    words = assemble(source,isa=isa)
    program_hex = program_hex or program.with_suffix('.hex')
    if words != [int(s, 16) for s in program_hex.read_text().split()]:
        raise ValueError('HEX y assembly no coinciden')
    labels, code = {}, []
    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if line.endswith(':'):
            labels[line[:-1]] = len(code) * 4
        elif line and not line.startswith('.'):
            code.append(dict(pc=len(code)*4, line=number, instruction=line))
    times32 = labels.get('signal_times32')
    if times32 is None:
        times32 = next(r['pc'] for r in code if r['instruction']=='add x10, x5, x5')
    boundaries = [
        (0, 0), (labels['wait_price']+16, 1), (labels['fill_buy'], 2),
        (labels['fill_buy_loop'], 3), (labels['fill_buy_done'], 2),
        (labels['fill_sell'], 4), (labels['fill_sell_loop'], 5),
        (labels.get('fill_sell_done',labels['fill_sell_loop']+12), 4), (labels['accounted'], 6),
        (times32, 7), (labels.get('signal_compare',times32+20), 8), (labels['propose_buy'], 9),
    ]
    if 'size_buy_loop' in labels:
        boundaries += [(labels['size_buy_loop'],10),(labels['size_buy_done'],9)]
    boundaries += [(labels['propose_sell'],11),(labels['publish'],0)]
    if boundaries != sorted(boundaries):
        raise ValueError('Cambio de estructura en D: revisar regiones del perfil')
    for row in code:
        group = next(g for pc, g in reversed(boundaries) if pc<=row['pc'])
        row.update(group=group, key=GROUPS[group][0], label=GROUPS[group][1])
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'pc_map.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(code[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(code)
    (output / 'profile_map.mem').write_text(''.join(f"{code[i]['group'] if i<len(code) else 0:08x}\n" for i in range(512)))
    (output / 'profile_metadata.json').write_text(json.dumps(dict(
        assembly_sha256=hashlib.sha256(source.encode()).hexdigest(),
        hex_sha256=hashlib.sha256(program_hex.read_bytes()).hexdigest(),
        groups=[dict(id=i,key=k,label=l,major=m) for i,(k,l,m) in enumerate(GROUPS)],
        labels=labels, clock_hz=25000000,
        attribution='ID valido: PC observado, incluyendo stalls; ID invalido: ultimo PC valido; ventana (byte_done, DECISION] para ciclos e incluye byte_done para IC, como metrica original.'
    ), ensure_ascii=False,indent=2)+'\n')


def csv_rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)


def analyze(source, destination):
    destination.mkdir(parents=True,exist_ok=True)
    metrics=csv_rows(source/'metrics.csv'); ticks=csv_rows(source/'profile_ticks.csv')
    if len(metrics)!=len(ticks): raise ValueError('Perfil incompleto')
    total_cycles=sum(int(r['cycles']) for r in metrics)
    total_ic=sum(int(r['instructions']) for r in metrics)
    for r,p in zip(metrics,ticks):
        if r['tick']!=p['tick'] or sum(int(p[f'g{g}_cycles']) for g in range(12))!=int(r['cycles']) or sum(int(p[f'g{g}_ic']) for g in range(12))!=int(r['instructions']):
            raise ValueError('La particion no conserva ciclos/IC por tick')
    details=[]
    for g,(key,label,major) in enumerate(GROUPS):
        cycles=sum(int(r[f'g{g}_cycles']) for r in ticks)
        ic=sum(int(r[f'g{g}_ic']) for r in ticks)
        details.append(dict(key=key,label=label,major=major,cycles=cycles,
                            fraction=cycles/total_cycles,cycles_per_tick=cycles/len(ticks),
                            instructions=ic,cpi=cycles/ic if ic else None))
    majors=[]
    for key in dict.fromkeys(d['major'] for d in details):
        ds=[d for d in details if d['major']==key]
        cycles=sum(d['cycles'] for d in ds)
        majors.append(dict(section=key,cycles=cycles,cycles_per_tick=cycles/len(ticks),fraction=cycles/total_cycles,instructions=sum(d['instructions'] for d in ds)))
    worst_index=max(range(len(metrics)),key=lambda i:int(metrics[i]['cycles']))
    worst=metrics[worst_index]
    worst_groups=[dict(key=k,cycles=int(ticks[worst_index][f'g{g}_cycles'])) for g,(k,_,_) in enumerate(GROUPS)]
    # Grupos disjuntos: nunca sumar ciclos dos veces al calcular f.
    targets={
        'shifter_solo_32p': ('times32',),
        'dimensionar_compra': ('size_buy_loop',),
        'ejecutar_compra': ('fill_buy_loop',),
        'ejecutar_venta': ('fill_sell_loop',),
        'dos_bucles_compra': ('fill_buy_loop','size_buy_loop'),
        'tres_bucles_ordenes': ('fill_buy_loop','fill_sell_loop','size_buy_loop'),
        'actualizar_ventana': ('window',),
    }
    amdahl=[]
    for target,keys in targets.items():
        f=sum(d['fraction'] for d in details if d['key'] in keys)
        f_worst=sum(d['cycles'] for d in worst_groups if d['key'] in keys)/int(worst['cycles'])
        for speed in (2,4,10,math.inf):
            amdahl.append(dict(target=target,local_speedup='infinito' if math.isinf(speed) else speed,
                               fraction=f,predicted_speedup=1/(1-f+f/speed),
                               fraction_worst_observed_tick=f_worst,
                               predicted_speedup_on_that_tick=1/(1-f_worst+f_worst/speed)))
    pcs={int(r['pc']):r for r in csv_rows(source/'pc_map.csv')}
    pc_rows=[]
    for r in csv_rows(source/'profile_pc.csv'):
        pc=int(r['pc']); m=pcs[pc]
        pc_rows.append(dict(**r,line=m['line'],instruction=m['instruction'],section=m['key'],fraction=int(r['cycles'])/total_cycles))
    pc_rows.sort(key=lambda r:int(r['cycles']),reverse=True)
    if sum(int(r['cycles']) for r in pc_rows)!=total_cycles or sum(int(r['instructions']) for r in pc_rows)!=total_ic:
        raise ValueError('El histograma independiente por PC no conserva ciclos/IC')
    write_csv(destination/'secciones.csv',majors)
    write_csv(destination/'detalle.csv',details)
    write_csv(destination/'amdahl.csv',amdahl)
    write_csv(destination/'instrucciones.csv',pc_rows)
    write_csv(destination/'peor_tick.csv',worst_groups)
    worst_majors={m:sum(w['cycles'] for w,(_,_,major) in zip(worst_groups,GROUPS) if major==m) for m in dict.fromkeys(d['major'] for d in details)}
    report=dict(ticks=len(ticks),total_cycles=total_cycles,total_instructions=total_ic,
                mean_cycles=total_cycles/len(ticks),cpi=total_cycles/total_ic,
                worst_tick=worst,worst_major_sections=worst_majors,major_sections=majors,detail=details,
                assumptions='Amdahl teorico: mismo reloj, otras secciones constantes, sin costos de integracion; no representa acelerador implementado. El tick de maxima latencia puede cambiar al optimizar.',
                idle_wait_omitted=json.loads((source/'result.json').read_text())['idle_wait_omitted'])
    (destination/'resumen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report,amdahl


def figures(report,amdahl,destination):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'ac4-profile-d-v1','font.family':'DejaVu Sans'})
    def save(fig,name):
        fig.savefig(destination/f'{name}.svg',metadata={'Date':None})
        svg=destination/f'{name}.svg'
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        fig.savefig(destination/f'{name}.png',dpi=180)
        plt.close(fig)
    labels={'io':'Recepción / publicación','contabilidad':'Contabilizar orden anterior','ventana':'Actualizar ventana SMA32','senal':'Calcular señal bursátil','cantidad_compra':'Dimensionar nueva compra','cantidad_venta':'Dimensionar nueva venta'}
    rows=sorted(report['major_sections'],key=lambda r:r['cycles'])
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    values=[r['cycles_per_tick'] for r in rows]
    bars=ax.barh([labels[r['section']] for r in rows],values,color='#2166ac')
    for b,r in zip(bars,rows):ax.text(b.get_width()+.5,b.get_y()+b.get_height()/2,f"{r['fraction']:.1%} · {r['cycles_per_tick']:.2f} ciclos",va='center',fontsize=10)
    ax.set_xlim(0,max(values)*1.65);ax.set_xlabel('Ciclos de servicio promedio por precio')
    ax.set_title(f"D · Dónde se consume el tiempo de respuesta\n{report['ticks']:,} precios · Espino original a 25 MHz".replace(',','.'),loc='left')
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    save(fig,'01_costo_por_seccion')
    names={'shifter_solo_32p':'Solo 32 × precio','dos_bucles_compra':'Dos bucles de compra','tres_bucles_ordenes':'Tres bucles de órdenes','actualizar_ventana':'Actualizar ventana SMA32'}
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    x=np.linspace(1,30,300)
    for target,name in names.items():
        r=next(r for r in amdahl if r['target']==target)
        f=r['fraction'];line,=ax.plot(x,1/(1-f+f/x),label=f"{name} · f={f:.1%}")
        ax.axhline(1/(1-f),color=line.get_color(),ls=':',lw=.8)
    ax.set_xlabel('Aceleración local hipotética');ax.set_ylabel('Aceleración total del servicio')
    ax.set_title('Ley de Amdahl · Predicción, antes de implementar hardware\nLíneas punteadas: límite ideal con aceleración local infinita',loc='left',fontsize=12)
    ax.grid(alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2,frameon=False,fontsize=9);ax.spines[['top','right']].set_visible(False)
    save(fig,'02_amdahl')
    fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
    colors=['#999999','#2166ac','#009e73','#cc79a7','#d55e00','#e6ab02']
    left=[0.,0.]
    for r,color in zip(report['major_sections'],colors):
        values=[100*r['fraction'],100*report['worst_major_sections'][r['section']]/int(report['worst_tick']['cycles'])]
        ax.barh(['Promedio de todos los precios','Tick con mayor latencia'],values,left=left,label=labels[r['section']],color=color)
        left=[a+b for a,b in zip(left,values)]
    ax.set_xlim(0,100);ax.set_xlabel('Distribución del tiempo de servicio (%)')
    ax.set_title(f"D · Promedio frente al máximo observado\n{report['mean_cycles']:.2f} ciclos promedio · {report['worst_tick']['cycles']} ciclos en tick {report['worst_tick']['tick']}",loc='left')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.19),ncol=2,frameon=False,fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    save(fig,'03_promedio_y_maximo')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    report,amdahl=analyze(args.source,args.destination)
    figures(report,amdahl,args.destination)
    print(json.dumps(dict(ticks=report['ticks'],mean_cycles=report['mean_cycles'],sections=report['major_sections']),ensure_ascii=False))


if __name__=='__main__': main()
