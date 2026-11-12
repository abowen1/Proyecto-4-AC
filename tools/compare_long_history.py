"""2.000 sesiones reales comunes por activo, A/D/DF; exploración en formato byte.

La escala usa el máximo del tramo completo: no es validación fuera de muestra.
Reproduce JSON archivados, no descarga datos ni altera los lotes anteriores.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from backtest import ROOT, official_rules, write_csv, buy_hold_reference
from compare_adaptive import simulate
from verify_market import verify

DEST = ROOT / 'docs/estrategia/historicos_2000_2026-11-12'
SYMBOLS = ('SPY', 'GOOGL', 'TSLA', 'TSM', 'NVDA', 'INTC')
VARIANTS = ('A', 'D', 'DF')
COUNT = 2000


def read_history(path):
    raw = json.loads(path.read_text(), parse_float=Decimal)
    result = raw['chart']['result'][0]
    quotes = result['indicators']['quote'][0]['close']
    assert len(quotes) == len(result['timestamp'])
    records = {}
    for t, close in zip(result['timestamp'], quotes):
        if close is None:
            continue
        date = datetime.fromtimestamp(t, timezone.utc).date().isoformat()
        if date <= '2025-12-31':
            assert date not in records and close > 0
            records[date] = Decimal(close)
    return records


def normalize(values):
    """Misma regla por activo; sin offset, interpolación, clipping ni logaritmo."""
    maximum = max(values)
    result = [int((p * 255 / maximum).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
              for p in values]
    if any(not 1 <= p <= 255 for p in result):
        raise ValueError('La serie no cabe sin clipping en un byte; no ejecutar')
    return result, maximum


def main():
    histories = {s:read_history(DEST / 'raw' / f'{s}.json') for s in SYMBOLS}
    dates = sorted(set.intersection(*(set(h) for h in histories.values())))[-COUNT:]
    assert len(dates) == COUNT and dates[-1] == '2025-12-31'
    summaries, replays, sources, graphs = [], [], {}, {}
    for symbol in SYMBOLS:
        folder = DEST / symbol
        folder.mkdir(parents=True, exist_ok=True)
        closes = [histories[symbol][d] for d in dates]
        prices, maximum = normalize(closes)
        raw_file = DEST / 'raw' / f'{symbol}.json'
        metadata = dict(symbol=symbol, source=f'https://finance.yahoo.com/quote/{symbol}/history/',
                        endpoint=f'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1451606400&period2=1767225600&interval=1d',
                        raw_sha256=hashlib.sha256(raw_file.read_bytes()).hexdigest(),
                        retrieved='2026-11-12', field='quote.close; base por acción provista ajustada por splits; no adjclose/dividendos',
                        observations=COUNT, start=dates[0], end=dates[-1], frequency='cierre diario',
                        selection='últimas 2000 fechas comunes hasta 2025-12-31',
                        transform='round_half_up(255 * close / max(close del tramo completo))',
                        max_close=str(maximum), min_price=min(prices), max_price=max(prices), clipped=0,
                        adjacent_unchanged=sum(a==b for a,b in zip(prices,prices[1:])),
                        preprocessing_uses_future=True,
                        limitation='Escala exploratoria usa el máximo futuro. Afecta señales, inventario y comisiones. No es una prueba financiera ciega ni comparable directamente con lotes a nivel 50/100.')
        sources[symbol] = metadata
        (folder/'fuente.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        write_csv(folder/'precios.csv',[dict(tick=i,date=d,close=str(c),price=p)
                                      for i,(d,c,p) in enumerate(zip(dates,closes,prices))])
        traces = {}
        for name in VARIANTS:
            summary, rows = simulate(prices, name)
            for row,date in zip(rows,dates):
                row['date'] = date
            summary.update(dataset=symbol, buy_hold_reference=buy_hold_reference(prices,official_rules()))
            summaries.append(summary)
            traces[name] = rows
            write_csv(folder/f'{name}.csv',rows)
            replays.append((symbol+'_'+name,rows))
        graphs[symbol] = dict(columns=['Fecha',*VARIANTS],
                             rows=[[d,*[traces[n][i]['equity'] for n in VARIANTS]] for i,d in enumerate(dates)])
    write_csv(DEST/'resumen.csv',summaries)
    verify(replays,DEST)
    config = dict(observations=COUNT,start=dates[0],end=dates[-1],rules=vars(official_rules()),
                  variants=VARIANTS,window=32,A_band=2,D_band=1,DF_band=1,
                  DF_filter='bloquea solo compras si SMA8 < SMA32',
                  normalization='255*close/max(close del tramo); redondeo half up; sin clipping',
                  preprocessing_uses_future=True,no_hard_stop=True,no_parameter_search=True,sources=sources,
                  source_sha256={f:hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                                 for f in ('compare_long_history.py','compare_adaptive.py','backtest.py','compare_protections.py','verify_market.py')})
    (DEST/'configuracion.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    (DEST/'graficos.json').write_text(json.dumps(graphs,ensure_ascii=False,separators=(',',':'))+'\n')
    report = ['# A, D y DF: 2.000 sesiones por activo', '',
              f'18 corridas sobre las mismas {COUNT} sesiones diarias comunes: {dates[0]} a {dates[-1]}. Activos: SPY, GOOGL, TSLA, TSM (ADR de TSMC), NVDA e INTC. Sin repetir ni interpolar observaciones. Fuentes Yahoo Finance y JSON originales archivados con hashes.', '',
              '## Qué significa 2.000 frente a 20.000', '',
              'El TB de Canvas tiene NTICKS=2000 por defecto; practica.csv tiene 20000 precios. Este lote iguala el número de puntos predeterminado, no la serie completa. Un tick es un precio recibido: no establece una duración de mercado. Aquí cada punto es un cierre diario; son casi ocho años. No equiparar 2000 días a 2000 transacciones de bolsa, ni a los períodos físicos de SPI de 10/1/0,1 ms.', '',
              '## Escala y alcance de la prueba', '',
              'La regla se fija antes de ejecutar las estrategias: precio = round_half_up(255 × cierre / máximo del tramo completo), independiente para cada activo. Misma regla para los seis. Preserva proporcionalidad salvo cuantización, sin desplazar el mínimo, sin logaritmos y sin clipping. Se usa close en la base por acción provista por Yahoo (splits ajustados), sin añadir dividendos. Los JSON completos descargados comienzan en 2016; solo se usan las últimas 2000 fechas comunes hasta el final de 2025.', '',
              '**La preparación de precios usa el máximo futuro de todo el tramo.** No es calibración con un año previo ni validación fuera de muestra. Se eligió esta normalización para alojar recorridos de hasta unas 65 veces entre mínimo y máximo (NVDA) en 1–255 sin saturarlos. No se buscaron factores que maximizaran resultados. Cada señal usa solo los precios normalizados actuales/pasados, pero la escala sí conoce el futuro y puede modificar las decisiones: estos resultados son exploratorios del juego, no un backtest financiero causal de punta a punta.', '',
              'La resolución de un byte pierde movimientos pequeños, especialmente en los primeros años de acciones que luego crecieron mucho. Los contadores adjacent_unchanged y rangos están en fuente.json. Los patrimonios no representan dólares reales ni se comparan directamente con los lotes a nivel 50/100. Ampliar la longitud no corrige estos límites, no garantiza más operaciones ni demuestra generalización a la serie desconocida de presentación.', '',
              '## Reglas conservadas', '',
              'A: SMA32, banda 2. D: SMA32, banda 1. DF: D más bloqueo de compras cuando SMA8 < SMA32; ventas sin cambios. Igualdad mantiene, promedio incluye precio actual, 31 ticks iniciales sin señal. Cantidades máximas 63 por orden; caja inicial 10000, comisión 5 por orden ejecutada, sin deuda/cortos, ejecución al precio siguiente, sin venta final forzada ni hard stop de patrimonio 20000. No se reinicia caja/inventario entre años. Solo se ejecutan las primeras 1999 decisiones propuestas.', '']
    for symbol in SYMBOLS:
        report += [f'## {symbol}', '', '| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima absoluta |', '|---|---:|---:|---:|---:|---:|']
        for s in sorted((s for s in summaries if s['dataset']==symbol),key=lambda s:s['equity'],reverse=True):
            report.append(f"| {s['label']} | {s['equity']} | {s['profit']:+d} | {s['orders']} | {s['commissions']} | {s['max_drawdown']} |")
        bh=next(s['buy_hold_reference'] for s in summaries if s['dataset']==symbol)
        report += ['',f'Comprar y mantener ideal del enunciado: {bh}. Compra al primer precio sin límite 63 ni desfase; no es una estrategia implementada por SPI.', '']
    report += ['## Validación y reproducción', '',
               'Las 18 trazas completas se reproducen con la tarea contable original de Canvas, comprobando caja, acciones, patrimonio, órdenes y caída por tick, más 20 casos límite: 36020 comparaciones. No se valida ejecución de A/D/DF en Espino ni deadlines. Los lotes anteriores quedan conservados. Estos activos comparten fechas y varios pertenecen al mismo sector; no son experimentos independientes.', '',
               'Reproducir desde la raíz: `python3 tools/compare_long_history.py`. Usa JSON archivados, Python estándar, iverilog y vvp. La referencia ideal se incluye para contexto, no se mezcla con las tres candidatas.']
    (DEST/'RESULTADOS.md').write_text('\n'.join(report)+'\n')
    print('Período',dates[0],dates[-1],COUNT,'sesiones')
    for s in summaries:
        print(s['dataset'],s['label'],'patrimonio',s['equity'],'órdenes',s['orders'],'DD',s['max_drawdown'])


if __name__=='__main__':
    main()
