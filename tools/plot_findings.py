"""Exporta gráficos SVG reproducibles para GitHub; no vuelve a simular."""
import csv
import os
from datetime import datetime
from pathlib import Path
from backtest import ROOT

os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator

DEST=ROOT/'docs/estrategia/recomendacion_2026-11-12/graficos'
COLORS={'A':'#0072B2','D':'#D55E00','DF':'#009E73'}


def draw(folder,names,title,filename,subtitle,with_target=False):
    fig,ax=plt.subplots(figsize=(10.5,4.8),layout='constrained')
    dated=False
    for name in names:
        rows=list(csv.DictReader((folder/f'{name}.csv').open()))
        dated='date' in rows[0]
        x=([datetime.fromisoformat(r['date']) for r in rows] if dated
           else [int(r['tick']) for r in rows])
        y=[int(r['equity']) for r in rows]
        base=name.removesuffix('_20k')
        label=base+(' + salida 20k' if name.endswith('_20k') else '')
        label+=f" · {y[-1]:,}".replace(',','.')
        ax.plot(x,y,label=label,color=COLORS[base],lw=1.4,
                linestyle='--' if name.endswith('_20k') else '-')
    ax.axhline(10000,color='#666666',lw=.7,linestyle=':',label='Capital inicial')
    if with_target:ax.axhline(20000,color='#999999',lw=.7,linestyle=':')
    ax.set_ylim(bottom=0)
    ax.set_xlim(x[0],x[-1])
    ax.set_title(title,loc='left',fontsize=14,pad=27)
    ax.text(0,1.025,subtitle,transform=ax.transAxes,fontsize=9,color='#555555')
    ax.set_ylabel('Patrimonio (unidades del juego)')
    ax.set_xlabel('Fecha / cierre diario' if dated else 'Tick')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{int(v):,}'.replace(',','.')))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
    if dated:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y',alpha=.2)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3,frameon=False,fontsize=9)
    fig.savefig(DEST/filename,format='svg',metadata={'Date':None})
    svg=DEST/filename
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    fig.savefig(DEST/Path(filename).with_suffix('.png'),dpi=150)
    plt.close(fig)


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    # Preserve actual line vertices and keep text readable in the exported SVG.
    plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'ac4-findings-v1',
                         'path.simplify':False,'font.family':'DejaVu Sans'})
    for symbol in ('SPY','GOOGL','TSLA','TSM','NVDA','INTC'):
        draw(ROOT/'docs/estrategia/historicos_2000_2026-11-12'/symbol,
             ('A','D','DF'),symbol+' · A, D y DF · 2.000 sesiones',f'largo_{symbol}.svg',
             '18-01-2018 a 31-12-2025 · escala al máximo del tramo (usa futuro) · sin hard stop')
    draw(ROOT/'docs/estrategia/protecciones_ad',('A','D','DF'),
         'Práctica Canvas · A, D y DF · 20.000 ticks','tb_20000.svg',
         'Precios originales · capital inicial 10.000 · comisión 5 · orden al precio siguiente')
    for symbol in ('TSLA','NVDA'):
        draw(ROOT/'docs/estrategia/salida_20000_2026-11-12'/symbol,
             ('A','D','DF','A_20k','D_20k','DF_20k'),
             symbol+' · continuar frente a salir al alcanzar 20.000',f'salida_{symbol}.svg',
             'Mismo lote largo exploratorio · líneas discontinuas: salida permanente',True)
    print('Gráficos SVG exportados:',len(list(DEST.glob('*.svg'))))


if __name__=='__main__':main()
