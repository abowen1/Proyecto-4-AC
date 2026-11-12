"""A, D, DF, Ad y Dd: práctica Canvas e históricos diarios independientes.

No descarga datos al reproducir: usa las respuestas originales archivadas de Yahoo.
No ejecuta estrategias en Espino; verifica contabilidad con la tarea Canvas en SV.
"""
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import csv
import hashlib
import json
from backtest import ROOT, official_rules, read_prices, run, write_csv, buy_hold_reference
from compare_protections import Protection
from verify_market import verify

DEST = ROOT / 'docs/estrategia/adaptativas_2026-11-12'
NAMES = ('A', 'D', 'DF', 'Ad', 'Dd', 'Mantener')


class AdaptiveReversion:
    """SMA32 ± k*desviación poblacional; k=1 (Ad), k=1/2 (Dd).

    Comparación exacta sin raíz ni división: (b*(S-N*p))² > a²*(N*Q-S²).
    La ventana incluye el precio recién recibido. Igualdad significa mantener.
    """
    def __init__(self, numerator=1, denominator=1, window=32):
        if numerator <= 0 or denominator <= 0 or window < 2:
            raise ValueError('k positivo y ventana >=2')
        self.a, self.b, self.n = numerator, denominator, window
        self.prices = deque()
        self.s = self.q = 0

    def observe(self, price):
        if len(self.prices) == self.n:
            old = self.prices.popleft()
            self.s -= old
            self.q -= old * old
        self.prices.append(price)
        self.s += price
        self.q += price * price
        if len(self.prices) < self.n:
            return 0
        d = self.s - self.n * price
        variance_n2 = self.n * self.q - self.s * self.s
        assert variance_n2 >= 0
        if (self.b * d) ** 2 <= self.a ** 2 * variance_n2:
            return 0
        return 1 if d > 0 else -1


def simulate(prices, name):
    rules = official_rules()
    if name == 'Mantener':
        return run(prices, 'mantener', rules)
    adaptive = AdaptiveReversion(1, 1 if name == 'Ad' else 2) if name in ('Ad', 'Dd') else None
    summary, rows = run(prices, 'reversion_media', rules,
                        dict(ventana=32, banda=2 if name == 'A' else 1),
                        Protection('F') if name == 'DF' else None,
                        signal_model=adaptive)
    summary.update(strategy=name, label=name)
    return summary, rows


def prepare_real(symbol, destination=DEST, anchor_level=100):
    if type(anchor_level) is not int or not 1 <= anchor_level <= 255:
        raise ValueError('Nivel de calibración entero entre 1 y 255')
    raw_file = destination / 'raw' / f'{symbol}.json'
    raw = json.loads(raw_file.read_text(), parse_float=Decimal)
    result = raw['chart']['result'][0]
    quotes = result['indicators']['quote'][0]['close']
    if len(quotes) != len(result['timestamp']):
        raise ValueError('timestamps/precios incompatibles')
    records = []
    missing = 0
    for timestamp, close in zip(result['timestamp'], quotes):
        if close is None:
            missing += 1
            continue
        date = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
        records.append((date, Decimal(close)))
    assert records == sorted(records) and len({d for d, _ in records}) == len(records)
    calibration = [(d, p) for d, p in records if d.startswith('2023-')]
    evaluation = [(d, p) for d, p in records if '2024-01-01' <= d <= '2025-12-31']
    if len(calibration) < 200 or len(evaluation) < 450:
        raise ValueError('Histórico insuficiente; no rellenar datos')
    anchor = max(p for _, p in calibration)
    normalized = []
    for tick, (date, close) in enumerate(evaluation):
        price = int((close * anchor_level / anchor).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        if not 1 <= price <= 255:
            raise ValueError(f'{symbol} fuera de rango: {date}, {price}; no clipping silencioso')
        normalized.append(dict(tick=tick, date=date, close=str(close), price=price))
    path = destination / symbol
    path.mkdir(parents=True, exist_ok=True)
    write_csv(path / 'precios.csv', normalized)
    meta = dict(symbol=symbol, source=f'https://finance.yahoo.com/quote/{symbol}/history/',
                endpoint=f'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1672531200&period2=1767225600&interval=1d',
                raw_sha256=hashlib.sha256(raw_file.read_bytes()).hexdigest(),
                retrieved='2026-11-12', frequency='1d, cierre; sin completar fines de semana',
                field='indicators.quote.close, no adjclose; sin pagos de dividendos',
                calibration_start=calibration[0][0], calibration_end=calibration[-1][0],
                calibration_count=len(calibration), calibration_max=str(anchor),
                transform=f'round_half_up({anchor_level} * close / max(close de 2023))',
                evaluation_start=normalized[0]['date'], evaluation_end=normalized[-1]['date'],
                observations=len(normalized), missing_source_closes=missing, clipped=0,
                min_price=min(r['price'] for r in normalized), max_price=max(r['price'] for r in normalized))
    (path / 'fuente.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    return [r['price'] for r in normalized], [r['date'] for r in normalized], meta


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    practice = ROOT / 'tb/practica.csv'
    prices = read_prices(practice)
    datasets = [('TB_20000', prices, None), ('TB_2000', prices[:2000], None)]
    sources = {}
    for symbol in ('SPY', 'GOOGL', 'TSLA'):
        p, dates, meta = prepare_real(symbol)
        datasets.append((symbol, p, dates))
        sources[symbol] = meta
    summaries, replays, graph_data = [], [], {}
    for dataset, p, dates in datasets:
        folder = DEST / dataset
        folder.mkdir(exist_ok=True)
        traces = {}
        for name in NAMES:
            summary, rows = simulate(p, name)
            summary.update(dataset=dataset, buy_hold_reference=buy_hold_reference(p, official_rules()))
            if dates:
                for row, date in zip(rows, dates):
                    row['date'] = date
            # Regression checks against the exact previously published traces.
            if dataset == 'TB_20000' and name in ('A', 'D', 'DF'):
                previous = ROOT / 'docs/estrategia/protecciones_ad' / f'{name}.csv'
                old = list(csv.DictReader(previous.open()))
                assert len(old) == len(rows)
                assert all({k: int(v) for k, v in a.items()} == b for a, b in zip(old, rows))
            write_csv(folder / f'{name}.csv', rows)
            summaries.append(summary)
            replays.append((dataset + '_' + name, rows))
            traces[name] = rows
        graph_data[dataset] = dict(prices=p, dates=dates, traces=traces)
    write_csv(DEST / 'resumen.csv', summaries)
    verify(replays, DEST)
    config = dict(rules=vars(official_rules()), variants=list(NAMES), window=32,
                  fixed_bands=dict(A=2, D=1, DF=1), adaptive_k=dict(Ad='1', Dd='1/2'),
                  trend_DF='bloquea solo compras si SMA8 < SMA32; ventas originales',
                  scope='Python causal + contabilidad SV; sin ejecución Espino ni deadlines',
                  no_hard_stop=True, no_parameter_search=True,
                  practice_sha256=hashlib.sha256(practice.read_bytes()).hexdigest(),
                  sources=sources,
                  code_sha256={f: hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                               for f in ('compare_adaptive.py', 'backtest.py', 'compare_protections.py', 'verify_market.py')})
    (DEST / 'configuracion.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n')
    report = ['# A, D, DF, Ad y Dd: prueba del 12 de noviembre', '',
              'Reglas fijadas antes de ejecutar; sin búsqueda automática de parámetros ni hard stop de patrimonio 20.000.', '',
              'A conserva SMA32/banda 2; D SMA32/banda 1; DF es D con bloqueo de compras si SMA8 < SMA32. Ad usa SMA32 ± 1 desviación estándar poblacional; Dd ± 0,5. Los 32 precios incluyen el actual; igualdad y calentamiento mantienen. Las cantidades son las mismas en todas las candidatas, hasta 63 por orden.', '',
              '## Datos y escala', '',
              'TB_20000 utiliza toda la práctica original; TB_2000 sus primeros 2.000 puntos (valor predeterminado del TB). SPY, GOOGL y TSLA usan 502 cierres diarios reales, del 02-01-2024 al 31-12-2025. Los 250 cierres de 2023 se usan exclusivamente para calibrar una escala fija: precio = redondeo mitad hacia arriba(100 × cierre / máximo de 2023). No se usa el máximo/mínimo del período evaluado; no hay interpolación, repetición ni clipping. El escalado tiene la misma regla para los tres activos, pero un factor propio calculado con su pasado.', '',
              'Fuentes: Yahoo Finance; respuestas originales JSON, hashes, URL y metadatos en raw/ y <símbolo>/fuente.json. Se usa close, no adjclose. No se añaden dividendos. Los precios convertidos son unidades del juego, no dólares: estos patrimonios no representan retornos de una inversión real. La cuantización, la comisión fija y el límite de cantidad afectan los resultados. Una ventana es 32 sesiones aquí; la unidad temporal de la práctica se desconoce. Esta comparación evalúa robustez en series distintas y no identifica la fuente original de Canvas.', '',
              '## Resultados', '']
    for dataset, _, _ in datasets:
        report += [f'### {dataset}', '', '| Variante | Patrimonio | Resultado | Órdenes | Comisiones | Caída máxima |', '|---|---:|---:|---:|---:|---:|']
        for s in sorted((s for s in summaries if s['dataset'] == dataset), key=lambda s:s['equity'], reverse=True):
            report.append(f"| {s['label']} | {s['equity']} | {s['profit']:+d} | {s['orders']} | {s['commissions']} | {s['max_drawdown']} |")
        bh = next(s['buy_hold_reference'] for s in summaries if s['dataset'] == dataset)
        report += ['', f'Comprar y mantener ideal del enunciado: {bh}. Compra al primer precio sin el límite de 63 ni el desfase SPI; es referencia, no candidata ejecutable.', '']
    report += ['## Exactitud y límites', '',
               'Caja inicial 10.000, comisión 5 por orden ejecutada, sin deuda/cortos, ejecución de la decisión al precio siguiente. El último patrimonio incluye inventario; no se fuerza venta final ni se ejecuta la última decisión pendiente. Se reproduce cada tick con la tarea ejecutar original de Canvas, incluidos casos límite. A/D/DF del TB completo deben coincidir byte por byte con las trazas previas.', '',
               'Ad/Dd comparan (b × (S − Np))² > a² × (NQ − S²), donde S=sum(precios), Q=sum(precios²), N=32 y k=a/b. El signo de S−Np decide compra/venta. No requieren raíz ni división en la referencia, pero sí multiplicaciones y atención al ancho de los intermedios. Aún no están implementadas en Espino ni validadas en tiempo. No asumir costo equivalente a A/D.', '',
               'Exploración: mirar estos resultados deja de reservar estos períodos como prueba final independiente. No elegir una variante solo porque gana en esta práctica conocida. Conviene comprobar después otros períodos separados antes de cerrar la selección.', '',
               'Reproducir desde la raíz: `python3 tools/compare_adaptive.py`. Requiere Python estándar, iverilog y vvp; los JSON ya están archivados, sin descarga nueva.']
    (DEST / 'RESULTADOS.md').write_text('\n'.join(report)+'\n')
    # Compact input for visualization generation, never used for accounting checks.
    compact = {}
    for dataset, data in graph_data.items():
        p, dates, traces = data['prices'], data['dates'], data['traces']
        keep = {0, len(p)-1}
        block = 160 if len(p) > 2000 else 1
        for start in range(0, len(p), block):
            ids = range(start, min(start+block, len(p)))
            for values in [p] + [[r['equity'] for r in traces[n]] for n in NAMES]:
                keep.add(min(ids, key=lambda i:values[i]))
                keep.add(max(ids, key=lambda i:values[i]))
        ids = sorted(keep)
        assert len(ids) <= 2000
        for name in NAMES:
            assert min(traces[name][i]['equity'] for i in ids) == min(r['equity'] for r in traces[name])
            assert max(traces[name][i]['equity'] for i in ids) == max(r['equity'] for r in traces[name])
        compact[dataset] = dict(columns=['Fecha' if dates else 'Tick', *NAMES],
                               rows=[[dates[i] if dates else i, *[traces[n][i]['equity'] for n in NAMES]] for i in ids],
                               prices=[[dates[i] if dates else i, p[i]] for i in ids],
                               ticks=len(p), shown=len(ids))
    (DEST / 'graficos.json').write_text(json.dumps(compact, ensure_ascii=False, separators=(',', ':'))+'\n')
    for s in summaries:
        print(s['dataset'],s['label'],s['equity'],s['orders'],s['max_drawdown'])


if __name__ == '__main__':
    main()
