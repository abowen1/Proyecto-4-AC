"""Archiva la evaluación de D sin cambios sobre la nueva práctica oficial Meta."""
import hashlib
import json
import math
from dataclasses import asdict
import os
from pathlib import Path
import shutil

from backtest import ROOT, official_rules, read_prices, run, write_csv, buy_hold_reference
from hardware_variants import VARIANTS, rtl_sources
from profile_d import analyze, csv_rows
from compare_hardware import TARGETS

DEST = ROOT/'docs/informe/05_meta_2026-11-17'
PREVIOUS = ROOT/'docs/informe/03_hardware_2026-11-12'
LABELS = dict(software='Software 102', shifter='Shifter elegido', qcap='QCAP')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    prices = read_prices(ROOT/'tb/practica_meta.csv')
    rules = official_rules()
    summary, rows = run(prices, 'reversion_media', rules, {'ventana':32, 'banda':1})
    write_csv(DEST/'D_python.csv', rows)
    q = (rules.cash-rules.commission)//prices[0]
    hold = [rules.cash-rules.commission-q*prices[0]+q*p for p in prices]
    peak = rules.cash
    max_dd = 0
    for wealth in hold:
        peak=max(peak, wealth);max_dd=max(max_dd, peak-wealth)
    reference = dict(series='Meta oficial, anuncio del 17/11',ticks=len(prices),
                     price_min=min(prices),price_max=max(prices),first_price=prices[0],last_price=prices[-1],
                     csv_sha256=digest(ROOT/'tb/practica_meta.csv'),rules=asdict(rules),D=summary,
                     no_trade=rules.cash,buy_hold=buy_hold_reference(prices,rules),
                     buy_hold_orders=1,buy_hold_commissions=rules.commission,buy_hold_max_drawdown=max_dd,
                     D_peak_equity=max(r['equity'] for r in rows))
    (DEST/'referencia.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n')
    profiles = {}
    records = []
    baserows = None
    for variant in VARIANTS:
        source = ROOT/'build/strategy_d'/f'meta_{variant}_20000'
        dest = DEST/'mediciones'/variant
        dest.mkdir(parents=True, exist_ok=True)
        for name in ('metrics.csv', 'profile_ticks.csv', 'profile_pc.csv', 'pc_map.csv',
                     'profile_metadata.json', 'result.json', 'program.hex'):
            shutil.copy2(source/name, dest/name)
        shutil.copy2(ROOT/'build'/f'meta_{variant}_20000.txt', dest/'ejecucion.txt')
        report = json.loads((dest/'result.json').read_text())
        assert report['metrics']['ticks'] == 20000
        assert report['hex_sha256'] == json.loads((PREVIOUS/'mediciones/practica_20000'/variant/'result.json').read_text())['hex_sha256']
        rows = csv_rows(dest/'metrics.csv')
        if baserows is None:
            baserows = rows
        for a, b in zip(baserows, rows):
            assert all(a[k] == b[k] for k in ('tick', 'price', 'next_decision', 'cash', 'shares'))
        profile, _ = analyze(dest, dest)
        profiles[variant] = profile
        build = json.loads((PREVIOUS/'compilacion'/variant/'imagen.json').read_text())
        records.append(dict(variant=variant, mean_cycles=profile['mean_cycles'],
                            max_cycles=int(profile['worst_tick']['cycles']),
                            mean_instructions=profile['total_instructions']/20000, cpi=profile['cpi'],
                            mean_us=profile['mean_cycles']*.04,
                            max_us=int(profile['worst_tick']['cycles'])*.04,
                            logic_cells=build['utilization']['ICESTORM_LC']['used'],
                            bram=build['utilization']['ICESTORM_RAM']['used'],
                            fmax_mhz=next(iter(build['fmax'].values()))['achieved']))
    for r in records:
        r['speedup'] = records[0]['mean_cycles']/r['mean_cycles']
        r['time_reduction'] = 1-r['mean_cycles']/records[0]['mean_cycles']
    write_csv(DEST/'comparacion_hardware.csv', records)
    amdahl = []
    for variant, keys in TARGETS.items():
        before = sum(d['cycles'] for d in profiles['software']['detail'] if d['key'] in keys)
        after = sum(d['cycles'] for d in profiles[variant]['detail'] if d['key'] in keys)
        f = before/profiles['software']['total_cycles']
        for local in (2, 4, 10, math.inf):
            amdahl.append(dict(variant=variant, fraction=f, local_speedup='infinito' if math.isinf(local) else local,
                               global_speedup=1/(1-f+f/local), kind='escenario hipotetico'))
        local = before/after
        amdahl.append(dict(variant=variant, fraction=f, local_speedup=local,
                           global_speedup=1/(1-f+f/local), kind='reconstruccion retrospectiva, no prediccion independiente'))
    write_csv(DEST/'amdahl_hardware.csv', amdahl)
    roof = []
    for variant, profile in profiles.items():
        cycles = next(d['cycles'] for d in profile['detail'] if d['key']=='window')
        ops = 2*20000-32
        data_bytes = (20000+20000-32)*4
        roof.append(dict(variant=variant, useful_add_sub=ops, data_bytes=data_bytes,
                         cycles=cycles, intensity_ops_per_byte=ops/data_bytes,
                         measured_ops_per_second=ops*25000000/cycles,
                         theoretical_peak_ops_per_second=12500000,
                         theoretical_data_port_bytes_per_second=100000000))
    write_csv(DEST/'roofline_sma32.csv', roof)
    canvas = ROOT/'build/canvas_final/practica_meta/2000_100000'
    dest = DEST/'canvas_2000_ronda3'
    dest.mkdir(exist_ok=True)
    for name in ('ejecucion.txt', 'result.json', 'decisiones.csv', 'program.hex', 'tb_canvas_configurado.sv'):
        shutil.copy2(canvas/name, dest/name)
    c = json.loads((canvas/'result.json').read_text())
    assert c['status']=='PASS' and c['canvas_checks']=='4/4'
    report = dict(series=reference, hardware=records, canvas=c, physical_reflash_required_by_announcement=False,
                  physical_spi_tested=False, production_code_changed=False,
                  full_series_idle_wait_omitted=True, clock_hz=25000000, report_date='2026-11-17')
    (DEST/'resultados.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    files = {ROOT/'tb/practica_meta.csv', ROOT/'tools/verify_strategy_d.py', ROOT/'tools/verify_canvas_final.py',
             ROOT/'tools/archive_meta.py', ROOT/'tools/assembler.py', ROOT/'tools/hardware_variants.py', ROOT/'Makefile', ROOT/'tools/backtest.py', ROOT/'tools/profile_d.py', ROOT/'tb/tb_strategy_d.sv', ROOT/'tb/tb_proyecto_4.sv'}
    for variant, config in VARIANTS.items():
        files.update(rtl_sources(variant))
        files.add(ROOT/config['program'])
    (DEST/'procedencia.json').write_text(json.dumps(dict(source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}), indent=2)+'\n')
    for p in DEST.rglob('*.csv'):
        p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
    for p in DEST.rglob('*.txt'):
        p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
    figures(reference, records, profiles)
    documentation(report)
    print(json.dumps(report, ensure_ascii=False))


def documentation(report):
    ref=report['series'];d=ref['D'];canvas=report['canvas'];rows=report['hardware']
    lines=['# Nueva práctica oficial Meta — 17 de noviembre de 2026', '',
           '**Resultado principal:** D sin cambios termina por debajo de no operar y de comprar y mantener. '
           'Las tres implementaciones ejecutan exactamente la misma estrategia; el hardware no explica esa pérdida.', '',
           '## Serie y alcance', '',
           'El archivo entregado por el usuario es `practica_meta.csv`, que el anuncio del curso identifica como '
           '20.000 precios de Meta, febrero–mayo de 2022, uno por minuto de mercado. El CSV solo contiene tick y precio: '
           'activo, período y frecuencia proceden del anuncio, no pueden inferirse de esas dos columnas. '
           'Se verificaron 20.000 filas consecutivas, mínimo 100, máximo 255, primer precio 165 y último 160. '
           f'SHA256 del archivo: `{ref["csv_sha256"]}`.', '',
           'La nueva serie está en `tb/practica_meta.csv`. La práctica anterior permanece intacta en `tb/practica.csv`; '
           'los resultados del 11–14/11 no se sobrescriben ni se mezclan con esta evaluación. '
           'D permanece fijada antes de ver los datos nuevos: SMA32, banda 1, sin retiro por patrimonio, '
           'sin filtros adicionales, caja inicial 10.000 y comisión 5. No se buscaron parámetros nuevos.', '',
           '## Resultado bursátil completo', '',
           '| Referencia | Patrimonio final | Órdenes | Comisiones | Máxima caída desde un peak |',
           '|---|---:|---:|---:|---:|',
           f'| D / SMA32 / banda 1 | **{d["equity"]}** | {d["orders"]} | {d["commissions"]} | {d["max_drawdown"]} |',
           '| No operar | 10000 | 0 | 0 | 0 |',
           f'| Comprar y mantener oficial | {ref["buy_hold"]} | 1 | 5 | {ref["buy_hold_max_drawdown"]} |', '',
           f'D pierde {10000-d["equity"]} frente a la caja inicial ({(d["equity"]/10000-1)*100:.2f} %) '
           f'y termina {ref["buy_hold"]-d["equity"]} por debajo de comprar y mantener. '
           f'Cierra con caja {d["cash"]} y {d["shares"]} acciones. '
           'Las comisiones son un costo observado importante; restarlas no equivale a simular la estrategia con comisión cero, '
           'porque la caja y las cantidades futuras también cambiarían. '
           'El benchmark comprar y mantener usa la fórmula oficial de Canvas, compra al primer precio y no '
           'representa una estrategia adicional ejecutada por SPI con desfase.', '',
           '![Patrimonio y precio de Meta](01_patrimonio_y_precio.png)', '',
           '## Equivalencia y tiempos de hardware', '',
           'Se ejecutaron los 20.000 precios en RTL por SPI para software optimizado, shifter y QCAP. '
           'En cada tick se comprueban la siguiente decisión, caja, acciones, una lectura y una respuesta, '
           'MISO sin X y deadline. Los HEX coinciden con los evaluados el 12/11: no hubo cambios de firmware. '
           'Los tres resultados contables y todas sus decisiones coinciden con Python y entre sí.', '',
           '| Variante | Promedio ciclos | Máximo observado | CPI de servicio | Reducción de tiempo | Celdas |',
           '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f'| {LABELS[r["variant"]]} | {r["mean_cycles"]:.5f} | {r["max_cycles"]} | {r["cpi"]:.5f} | {r["time_reduction"]:.2%} | {r["logic_cells"]}/1280 |')
    lines += ['', 'Todas las variantes conservan 25 MHz y 12 BRAM. Área y Fmax se reutilizan de la compilación '
              'archivada del 12/11 porque RTL e imágenes de programa no cambian al cambiar los precios externos. '
              'Cada perfil conserva exactamente los ciclos e instrucciones, por tick, por sección y por PC. '
              'El CSV de Amdahl actualiza las fracciones con Meta; la reconstrucción con costo local medido '
              'se distingue de los escenarios hipotéticos. El roofline define como operaciones las sumas/restas '
              'del anillo SMA32 y cuenta solo bytes de su puerto de datos, sin mezclarlo con decisiones por segundo.', '',
              '**Método de tiempo:** las corridas completas omiten espera ociosa entre precios (`--fast`); '
              'verifican equivalencia y ventana de servicio, pero no constituyen 20.000 ticks con período fijo. '
              'Los máximos observados no se presentan como una demostración formal del peor caso posible.', '',
              '![Tiempos con Meta](02_tiempos_hardware.png)', '',
              '![Perfil por sección](03_perfil_por_seccion.png)', '',
              '## Maestra simulada de Canvas: ronda rápida', '',
              f'El testbench oficial configurado con la nueva serie y shifter aprobó **{canvas["canvas_checks"]} chequeos** '
              f'en los primeros 2.000 precios, con período fijo de 100.000 ns. '
              f'Patrimonio de ese tramo: **{canvas["expected_summary"]["equity"]}**, '
              f'{canvas["expected_summary"]["orders"]} órdenes. '
              'El runner compara además cada decisión ejecutada y estado contable con Python. '
              'No se deben confundir estos resultados parciales con los de 20.000 precios. '
              'Las tareas SPI, la contabilidad y los cuatro chequeos del testbench se conservan; '
              'solo se configuran rutas/parámetros y se adapta `localparam string` a Icarus.', '',
              '## Qué significa para la placa del equipo', '',
              '**El anuncio no obliga a reprogramar.** La imagen cargada el 14/11 acepta 1–255 y recibe los precios '
              'por SPI: no contiene ninguna serie precargada. El nuevo CSV se cambia en el simulador o en la maestra, '
              'no dentro del bitstream. En esta evaluación no se programó la placa ni se modificaron D o el shifter. '
              'El grupo puede probar la conexión con el curso usando la versión que ya tiene.', '',
              '**Sí conviene reabrir la evaluación de la estrategia bursátil antes de competir.** '
              'El resultado anterior de 17.909 no describe esta práctica nueva. Una serie no demuestra que D '
              'sea universalmente mala, pero esta pérdida es evidencia que no se debe ocultar ni resolver ajustando '
              'a ciegas parámetros para memorizar Meta. Mantener el shifter no obliga a mantener una estrategia '
              'si posteriormente el equipo decide cambiarla. Cualquier cambio bursátil requerirá nueva equivalencia '
              'y, entonces sí, cargar otro programa en la placa.', '',
              'El intercambio físico con la maestra sigue pendiente. No se presenta ninguna de estas simulaciones '
              'como una ronda física. Confirmar con el curso inicio/reinicio entre rondas; los botones no reinician '
              'el estado bursátil de la imagen actual.', '',
              '## Reproducción y evidencia', '',
              '```sh', 'make test-final   # nueva Meta, 2.000 precios, período fijo más rápido',
              'make verify-meta  # 3 implementaciones completas + Canvas + archivo y gráficos',
              '# Práctica histórica, explícitamente:',
              'python3 tools/verify_canvas_final.py --series tb/practica.csv', '```', '',
              '`test-final` usa ahora Meta por defecto. Los demás scripts históricos mantienen sus '
              'valores predeterminados anteriores: para nuevas pruebas usar `--series tb/practica_meta.csv`. '
              'El objetivo `verify-meta` ya lo hace explícitamente.', '',
              '`D_python.csv` y `referencia.json` contienen el resultado financiero. '
              '`mediciones/<variante>/` contiene todos los ticks, perfiles, instrucciones, resultados y logs; '
              '`canvas_2000_ronda3/` guarda el testbench configurado y su salida. '
              '`comparacion_hardware.csv`, `amdahl_hardware.csv`, `roofline_sma32.csv` y `procedencia.json` '
              'permiten reconstruir las tablas y comprobar las fuentes. Las tres figuras tienen copia PNG y SVG.', '']
    (DEST/'README.md').write_text('\n'.join(lines))


def figures(reference, records, profiles):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'build/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter
    plt.rcParams.update({'svg.fonttype':'none', 'svg.hashsalt':'ac4-meta-20261117', 'font.family':'DejaVu Sans'})

    def save(fig, name):
        fig.savefig(DEST/(name+'.png'), dpi=180)
        p=DEST/(name+'.svg');fig.savefig(p, metadata={'Date':None})
        p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
        plt.close(fig)

    prices = read_prices(ROOT/'tb/practica_meta.csv')
    _, rows = run(prices, 'reversion_media', official_rules(), {'ventana':32,'banda':1})
    q = (10000-5)//prices[0]
    hold = [10000-5-q*prices[0]+q*p for p in prices]
    fig, (ax, px) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout='constrained', gridspec_kw={'height_ratios':[2, 1]})
    ax.plot([r['equity'] for r in rows], color='#0072b2', lw=1.25, label=f"D sin cambios · final {rows[-1]['equity']:,}")
    ax.plot(hold, color='#d55e00', lw=1.05, label=f"Comprar y mantener (benchmark oficial) · final {hold[-1]:,}")
    ax.axhline(10000, color='#666666', ls='--', label='No operar · 10.000')
    ax.set_ylabel('Patrimonio');ax.legend(loc='upper left', fontsize=9)
    ax.set_title('Nueva práctica oficial Meta · 20.000 ticks\nD: SMA32, banda 1, comisión 5, ejecución al precio siguiente', loc='left')
    px.plot(prices, color='#444444', lw=.8);px.set_ylabel('Precio normalizado');px.set_xlabel('Tick de la serie de práctica')
    for a in (ax, px):
        a.grid(alpha=.2);a.spines[['top','right']].set_visible(False);a.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    save(fig, '01_patrimonio_y_precio')
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.8), layout='constrained')
    for ax, field, title in zip(axs, ('mean_cycles','max_cycles'), ('Promedio de servicio','Máximo observado')):
        vals=[r[field] for r in records];bars=ax.bar([LABELS[r['variant']] for r in records], vals, color=['#999999','#0072b2','#d55e00'])
        for b,v in zip(bars, vals):ax.text(b.get_x()+b.get_width()/2, b.get_height()+max(vals)*.025, f'{v:.2f}' if field=='mean_cycles' else str(v), ha='center')
        ax.set_ylim(0,max(vals)*1.18);ax.set_ylabel('Ciclos');ax.set_title(title,loc='left');ax.tick_params(axis='x',rotation=12);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('D · misma serie Meta y mismas decisiones · reloj de 25 MHz');save(fig,'02_tiempos_hardware')
    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    colors=['#999999','#0072b2','#009e73','#cc79a7','#d55e00','#e6ab02'];left=[0.,0.,0.]
    for section, color in zip(profiles['software']['major_sections'], colors):
        values=[next(d['cycles_per_tick'] for d in profiles[v]['major_sections'] if d['section']==section['section']) for v in VARIANTS]
        ax.barh(list(LABELS.values()), values, left=left, label=section['section'], color=color)
        left=[a+b for a,b in zip(left,values)]
    ax.set_xlabel('Ciclos de servicio promedio por precio');ax.set_title('Meta · perfil por sección de las tres implementaciones',loc='left')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=3,frameon=False);ax.spines[['top','right']].set_visible(False);save(fig,'03_perfil_por_seccion')


if __name__ == '__main__':
    main()
