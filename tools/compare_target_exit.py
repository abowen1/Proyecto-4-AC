"""Salida permanente al observar patrimonio >=20.000; referencia, no assembly."""
import csv
import hashlib
import json
from backtest import ROOT, official_rules, read_prices, run, size_order, write_csv
from compare_protections import Protection
from verify_market import verify

DEST = ROOT / 'docs/estrategia/salida_20000_2026-11-12'
VARIANTS = ('A', 'D', 'DF')


class TargetExit:
    def __init__(self, base=None, target=20000):
        if type(target) is not int or target <= 0:
            raise ValueError('Objetivo positivo entero')
        self.base, self.target = base, target
        self.trigger = self.flat = None
        self.tick = -1

    def decide(self, signal, market, price, fill):
        self.tick += 1
        if self.trigger is None and market.equity >= self.target:
            self.trigger = dict(tick=self.tick, equity=market.equity,
                                cash=market.cash, shares=market.shares, price=price)
        if self.trigger is not None:
            if market.shares:
                return 0x80 | min(63, market.shares)
            if self.flat is None:
                self.flat = dict(tick=self.tick, cash=market.cash)
            return 0
        return (size_order(signal, market, price) if self.base is None
                else self.base.decide(signal, market, price, fill))


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    datasets = [('TB_20000', ROOT/'tb/practica.csv',
                 ROOT/'docs/estrategia/protecciones_ad')]
    for symbol in ('SPY','GOOGL','TSLA','TSM','NVDA','INTC'):
        folder = ROOT/'docs/estrategia/historicos_2000_2026-11-12'/symbol
        datasets.append((symbol,folder/'precios.csv',folder))
    summaries, replays, sources = [], [], {}
    for dataset, price_file, prior in datasets:
        prices = read_prices(price_file)
        input_rows = list(csv.DictReader(price_file.open()))
        dates = [r.get('date') for r in input_rows]
        sources[dataset] = dict(price_sha256=hashlib.sha256(price_file.read_bytes()).hexdigest(),
                                source=str(price_file.relative_to(ROOT)))
        folder = DEST/dataset
        folder.mkdir(exist_ok=True)
        for name in VARIANTS:
            baseline_rows = None
            for exit_enabled in (False,True):
                base = Protection('F') if name=='DF' else None
                policy = TargetExit(base) if exit_enabled else base
                summary,rows=run(prices,'reversion_media',official_rules(),
                                 dict(ventana=32,banda=2 if name=='A' else 1),policy)
                if not exit_enabled:
                    baseline_rows=[dict(r) for r in rows]
                    old=list(csv.DictReader((prior/f'{name}.csv').open()))
                    assert len(old)==len(rows)
                    assert all(all(int(a[k])==b[k] for k in b) for a,b in zip(old,rows))
                elif policy.trigger is None:
                    assert rows==baseline_rows
                if dates[0]:
                    for r,d in zip(rows,dates):r['date']=d
                label=name+'_20k' if exit_enabled else name
                trigger=policy.trigger if exit_enabled else None
                flat=policy.flat if exit_enabled else None
                summary.update(strategy=label,label=label,dataset=dataset,
                               target=20000 if exit_enabled else 0,
                               triggered=bool(trigger),trigger_tick=trigger['tick'] if trigger else '',
                               trigger_date=dates[trigger['tick']] if trigger and dates[0] else '',
                               trigger_equity=trigger['equity'] if trigger else '',
                               liquidation_tick=flat['tick'] if flat else '',
                               liquidation_date=dates[flat['tick']] if flat and dates[0] else '',
                               liquidation_cash=flat['cash'] if flat else '',
                               delta_vs_base=summary['equity']-baseline_rows[-1]['equity'])
                write_csv(folder/f'{label}.csv',rows)
                summaries.append(summary)
                replays.append((dataset+'_'+label,rows))
    write_csv(DEST/'resumen.csv',summaries)
    verify(replays,DEST)
    config=dict(target='patrimonio observado >=20000, no ganancia neta ni solo caja',
                rule='activa latch permanente; vende hasta 63 por tick desde siguiente precio; no recompra nunca',
                warning='no garantiza liquidar en 20000 por comisiones, desfase y variaciones durante ventas',
                scope='TB completo y seis históricos largos exploratorios; no modifica estrategias base ni assembly',
                sources=sources,source_sha256={f:hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                                              for f in ('compare_target_exit.py','backtest.py','compare_protections.py')})
    (DEST/'configuracion.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n')
    report=['# Salida permanente al alcanzar patrimonio 20.000', '',
            'Regla fijada antes de correr: al observar caja + acciones*precio >=20.000 después de ejecutar la orden pendiente, activar salida permanente. Desde esa decisión se venden hasta 63 acciones por tick al precio siguiente, aun si rebota o cae durante la liquidación. Cuando no quedan acciones, mantener efectivo para siempre. Si no llega al objetivo, seguir con la estrategia base. No se conoce el final de la serie para tomar decisiones.', '',
            'No equivale a retirar exactamente 20.000: puede venderse por menos o por más, y hay comisiones. Si se dispara en el último tick no hay tiempo de ejecutar la venta. No se vende todo en un único tick cuando hay más de 63 acciones. No se agregó al programa Espino ni a los resultados anteriores.', '',
            'Datos: TB original completo y las seis series largas de 2.000 sesiones. Estas últimas usan escala al máximo del tramo completo y contienen información futura en el preprocesamiento; son exploratorias, no prueba final independiente. Se conserva el capital entre años dentro de cada corrida; cada activo y variante empieza con 10.000.', '']
    for dataset,_,_ in datasets:
        report += [f'## {dataset}', '', '| Base | Sin salida | Con salida 20k | Diferencia | Activó | Tick activación | Fecha activación | Patrimonio al activar | Caja al terminar liquidación |', '|---|---:|---:|---:|---|---:|---|---:|---:|']
        for name in VARIANTS:
            original=next(s for s in summaries if s['dataset']==dataset and s['label']==name)
            stopped=next(s for s in summaries if s['dataset']==dataset and s['label']==name+'_20k')
            report.append(f"| {name} | {original['equity']} | {stopped['equity']} | {stopped['delta_vs_base']:+d} | {'sí' if stopped['triggered'] else 'no'} | {stopped['trigger_tick']} | {stopped['trigger_date']} | {stopped['trigger_equity']} | {stopped['liquidation_cash']} |")
        report.append('')
    report += ['## Validación y reproducción', '',
               'Las bases se contrastan con cada tick de sus trazas anteriores. Si no se activa el objetivo, la traza debe ser idéntica. Las 42 corridas completas más 20 casos límite se verifican con la tarea contable original de Canvas (192.020 ticks). Ver configuración, resumen, trazas y validacion_contabilidad.json.', '',
               'Reproducir: `python3 tools/compare_target_exit.py`. Requiere los lotes ya archivados, Python estándar, iverilog y vvp.']
    (DEST/'RESULTADOS.md').write_text('\n'.join(report)+'\n')
    for s in summaries:
        if s['target']:
            print(s['dataset'],s['label'],s['equity'],'delta',s['delta_vs_base'],'trigger',s['trigger_date'] or s['trigger_tick'])


if __name__=='__main__':main()
