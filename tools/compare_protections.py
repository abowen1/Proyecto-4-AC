"""A/D y tres protecciones separadas: pánico, tendencia, exposición."""
from collections import deque
from pathlib import Path
import csv
import hashlib
import json
from backtest import ROOT, official_rules, read_prices, run, size_order, write_csv
from verify_market import verify

VARIANTS = ('A', 'D', 'AP', 'DP', 'AF', 'DF', 'AE', 'DE')


class Protection:
    def __init__(self, mode):
        if mode not in ('P','F','E'):
            raise ValueError(mode)
        self.mode = mode
        self.prices = deque(maxlen=32)
        self.peak = 0
        self.panic = False
        self.cooldown = 0
        self.events = 0

    def decide(self, signal, market, price, fill):
        self.prices.append(price)
        if self.mode == 'P':
            if market.shares == 0:
                self.peak = 0
                if self.panic:
                    self.panic = False
                    self.cooldown = 32
                    return 0
                if self.cooldown:
                    self.cooldown -= 1
                    return 0
            else:
                self.peak = max(self.peak, price)
                if not self.panic and price * 100 <= self.peak * 90:
                    self.panic = True
                    self.events += 1
                if self.panic:
                    return 0x80 | min(63, market.shares)
        elif self.mode == 'F':
            if signal > 0 and len(self.prices) == 32:
                if sum(list(self.prices)[-8:]) * 32 < sum(self.prices) * 8:
                    self.events += 1
                    return 0
        elif self.mode == 'E':
            # Objetivo 50% al precio observado, reservando comisión. Se corrige
            # en ticks posteriores si el precio de ejecución cambia el peso.
            target = max(0, (market.equity - market.rules.commission) // (2 * price))
            if market.shares > target:
                self.events += 1
                return 0x80 | min(63, market.shares - target)
            if signal > 0:
                base = size_order(signal, market, price) & 63
                q = min(base, max(0, target - market.shares))
                if q < base:
                    self.events += 1
                return 0x40 | q if q else 0
        return size_order(signal, market, price)


def main():
    destination = ROOT / 'docs/estrategia/protecciones_ad'
    destination.mkdir(parents=True, exist_ok=True)
    series = ROOT/'tb/practica.csv'
    prices, rules = read_prices(series), official_rules()
    summaries, replays = [], []
    for name in VARIANTS:
        mode = name[1:]
        policy = Protection(mode) if mode else None
        summary, rows = run(prices, 'reversion_media', rules,
                            dict(ventana=32,banda=2 if name[0]=='A' else 1), policy)
        summary.update(strategy=name,label=name,protection=mode or 'ninguna',
                       events=policy.events if policy else 0)
        summaries.append(summary)
        replays.append((name, rows))
        write_csv(destination/f'{name}.csv',rows)
        if not mode:
            previous=ROOT/f'docs/estrategia/reversion_abcde/reversion_{name}.csv'
            if previous.exists():
                old=list(csv.DictReader(previous.open()))
                assert len(old)==len(rows)
                assert all({k:int(v) for k,v in a.items()}==b for a,b in zip(old,rows))
    write_csv(destination/'resumen.csv',summaries)
    verify(replays,destination)
    config=dict(variants=VARIANTS,rules=vars(rules),ticks=len(prices),
                base=dict(ventana=32,banda_A=2,banda_D=1),
                panic=dict(caida_porcentual=10,referencia='máximo del precio observado mientras haya inventario',
                           salida='vender hasta quedar sin acciones, máximo 63 por tick',
                           reentrada='esperar 32 ticks completos tras quedar sin acciones y luego seguir señal base'),
                trend=dict(corta=8,larga=32,regla='bloquear compras si SMA8 < SMA32; no cambia ventas'),
                exposure=dict(objetivo_porcentual=50,regla='limitar compras y vender exceso respecto del objetivo con precio actual y comisión reservada; corrección hasta 63 por tick'),
                series_sha256=hashlib.sha256(series.read_bytes()).hexdigest(),
                source_sha256={f:hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                               for f in ('backtest.py','compare_protections.py','verify_market.py')})
    (destination/'configuracion.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n')
    report=['# A/D: pánico, filtro y exposición', '',
            'Mismos 20.000 precios, capital 10.000, comisión 5 y desfase de ejecución de un tick. A/D coinciden exactamente con las corridas anteriores.', '',
            '| Variante | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Caída máxima desde peak |',
            '|---|---:|---:|---:|---:|---:|']
    for r in summaries:
        report.append(f"| {r['label']} | {r['equity']} | {r['profit']:+d} | {r['orders']} | {r['commissions']} | {r['max_drawdown']} |")
        print(r['label'], 'patrimonio',r['equity'],'órdenes',r['orders'],'comisión',r['commissions'],'drawdown',r['max_drawdown'])
    report += ['', '## Reglas elegidas antes de correr este lote', '',
               '- A: SMA32, banda 2; D: SMA32, banda 1. Se mantienen reglas originales de señales y cantidades.',
               '- AP/DP: caída de al menos 10% desde el máximo del precio observado durante una posición con inventario. Liquida en órdenes sucesivas de hasta 63, sin recomprar durante la liquidación. Después de quedar sin acciones, espera 32 ticks completos antes de habilitar otra compra. El máximo se reinicia al quedar sin acciones. El disparo no compara patrimonio ni precio medio de compra.',
               '- AF/DF: bloquea nuevas compras cuando SMA8 < SMA32. No fuerza ventas: las ventas siguen la señal base. Los promedios incluyen el último precio.',
               '- AE/DE: objetivo de exposición máximo 50% del patrimonio al precio observado. Calcula acciones objetivo como floor((patrimonio − comisión)/(2 × precio)). Limita nuevas compras y vende excesos en órdenes de hasta 63. El precio siguiente y el límite por orden pueden impedir cumplir el 50% de inmediato. La corrección puede generar ventas pequeñas y más comisiones.',
               '- Cada protección se aplica por separado; ninguna variante mezcla P/F/E. Pánico incluye espera para evitar recomprar inmediatamente después de liquidar; no se buscó el mejor porcentaje ni la mejor espera.', '',
               '## Validación y límites', '',
               'Las órdenes de las ocho variantes se reprodujeron con la tarea contable exacta de Canvas, comparando caja, acciones, patrimonio, órdenes y drawdown por tick. A/D se contrastaron con sus trazas anteriores. No son implementaciones en Espino ni resultados de plazos de hardware.', '',
               'El riesgo se mide aquí como caída absoluta máxima desde un máximo anterior de patrimonio, no como porcentaje. El patrimonio final incluye acciones valoradas al último precio; no se fuerza liquidación final.', '',
               'Reproducir con `make compare-protections`. Se mantienen los lotes anteriores. Evaluación exploratoria sobre la misma serie conocida; sin búsqueda automática de parámetros ni validación en otra serie.']
    (destination/'RESULTADOS.md').write_text('\n'.join(report)+'\n')


if __name__=='__main__':
    main()
