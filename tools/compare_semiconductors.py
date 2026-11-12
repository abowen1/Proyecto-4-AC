"""A/D/DF sin cambios: TSM, NVDA, INTC y controles anteriores a escala común 50."""
import hashlib
import json
from backtest import ROOT, official_rules, write_csv, buy_hold_reference
from compare_adaptive import prepare_real, simulate
from verify_market import verify

DEST = ROOT / 'docs/estrategia/semiconductores_2026-11-12'
SYMBOLS = ('TSM', 'NVDA', 'INTC', 'SPY', 'GOOGL', 'TSLA')
VARIANTS = ('A', 'D', 'DF')


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    summaries, replays, sources = [], [], {}
    for symbol in SYMBOLS:
        prices, dates, metadata = prepare_real(symbol, DEST, anchor_level=50)
        sources[symbol] = metadata
        for name in VARIANTS:
            summary, rows = simulate(prices, name)
            for row, date in zip(rows, dates):
                row['date'] = date
            summary.update(dataset=symbol, buy_hold_reference=buy_hold_reference(prices, official_rules()))
            write_csv(DEST / symbol / f'{name}.csv', rows)
            summaries.append(summary)
            replays.append((symbol + '_' + name, rows))
    write_csv(DEST / 'resumen.csv', summaries)
    verify(replays, DEST)
    config = dict(variants=VARIANTS, symbols=SYMBOLS, rules=vars(official_rules()),
                  parameters=dict(window=32, A_band=2, D_band=1, DF_band=1,
                                  DF_filter='solo bloquea compras si SMA8 < SMA32'),
                  calibration_level=50, previous_level=100, no_hard_stop=True,
                  change_reason='TSM y NVDA exceden 255 con la escala anterior. Se reduce el nivel común a 50 y se repiten los tres controles; no se ajustaron parámetros de estrategias ni se eligió por patrimonio.',
                  selection_caveat='El cambio de escala se decidió tras inspeccionar rangos. No es una prueba final ciega ni comparable directamente con cifras previas de nivel 100.',
                  sources=sources,
                  source_sha256={f:hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest()
                                 for f in ('compare_semiconductors.py','compare_adaptive.py','backtest.py','compare_protections.py','verify_market.py')})
    (DEST / 'configuracion.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n')
    report = ['# A, D y DF: TSMC, NVIDIA e Intel', '',
              '18 corridas: TSM/NVDA/INTC y controles SPY/GOOGL/TSLA. Solo A, D y DF. Sin búsqueda de parámetros, variantes nuevas ni hard stop en 20.000.', '',
              '## Protocolo y cambio de escala', '',
              'Se usan 502 cierres diarios por activo (02-01-2024 a 31-12-2025). Calibración: 250 cierres de 2023. TSM es el ADR estadounidense de TSMC. Fuente Yahoo Finance, campo close (histórico provisto con ajustes por splits; no adjclose ni pagos de dividendos). JSON originales, URL, hashes y precios convertidos archivados. El split 10:1 de NVDA en junio de 2024 no se interpreta como un desplome de precio: el proveedor expresa el histórico en la misma base por acción. Referencia del evento: https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2025/', '',
              'Con la regla anterior, 100*cierre/máximo_2023, TSM llegaría a 289 y NVDA a 411: no caben en 1–255. Este lote usa round_half_up(50*cierre/máximo_2023) para TODOS los activos, sin clipping, repetir ni interpolar datos. El cambio de nivel se decidió después de inspeccionar los rangos de datos, para admitirlos en el protocolo; no se probaron niveles para escoger el de mayor patrimonio. La transformación de cada tick usa solo su precio y una constante calculada con 2023.', '',
              'La escala no es inocua: cambia la banda relativa de las estrategias, los redondeos, el inventario y las comisiones relativas. Por eso se repitieron también SPY/GOOGL/TSLA con nivel 50. Comparar dentro de este lote; no mezclar sus cifras con las de nivel 100. Ambos lotes se conservan. Los patrimonios son unidades del juego, no dólares ni retornos financieros reales.', '',
              'A: SMA32/banda 2. D: SMA32/banda 1. DF: D más filtro que bloquea compras si SMA8 < SMA32; no fuerza ventas. Media incluye el último precio, calentamiento 32, desigualdad estricta. Caja 10.000, comisión 5 por orden efectiva, cantidades hasta 63, no cortos/deuda, orden ejecutada al precio siguiente. Sin liquidación final. Los parámetros de las tres candidatas son los mismos de los lotes previos.', '']
    for symbol in SYMBOLS:
        report += [f'## {symbol}', '', '| Variante | Patrimonio final | Resultado | Órdenes | Comisiones | Caída máxima desde peak |', '|---|---:|---:|---:|---:|---:|']
        for s in sorted((s for s in summaries if s['dataset']==symbol),key=lambda s:s['equity'],reverse=True):
            report.append(f"| {s['label']} | {s['equity']} | {s['profit']:+d} | {s['orders']} | {s['commissions']} | {s['max_drawdown']} |")
        bh=next(s['buy_hold_reference'] for s in summaries if s['dataset']==symbol)
        report += ['',f'Benchmark ideal comprar y mantener: {bh}. Compra al primer precio sin límite 63 ni desfase SPI; referencia del enunciado, no estrategia implementada.', '']
    report += ['## Validación y límites', '',
               'Cada decisión se reprodujo con la tarea contable original de Canvas. Se verifican caja, acciones, patrimonio, órdenes y caída máxima en cada tick; se añaden 20 casos límite. Ver validacion_contabilidad.json. No se ejecutaron las estrategias en Espino ni se midieron deadlines. Los datos y reglas de los lotes anteriores se conservan.', '',
               'Los tres activos nuevos pertenecen al mismo sector y las seis pruebas usan el mismo período: no son seis experimentos de mercado independientes. La escala cambia respecto del primer lote y estos períodos ya están explorados; todavía no hay prueba final reservada ni selección definitiva de estrategia.', '',
               'Reproducir: `python3 tools/compare_semiconductors.py` desde la raíz. Python estándar, iverilog y vvp; utiliza los JSON archivados sin descargar de nuevo.']
    (DEST / 'RESULTADOS.md').write_text('\n'.join(report)+'\n')
    for s in summaries:
        print(s['dataset'],s['label'], 'patrimonio',s['equity'],'órdenes',s['orders'],'DD',s['max_drawdown'])


if __name__ == '__main__':
    main()
