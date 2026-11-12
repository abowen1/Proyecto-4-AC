"""Ejecuta D en RTL sin modificar el procesador; comprueba cada tick por SPI."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

from backtest import ROOT, read_prices, run, official_rules


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--series', type=Path, default=ROOT / 'tb/practica.csv')
    source.add_argument('--edges', action='store_true', help='816 precios artificiales extremos; prueba tecnica, no evaluacion bursatil')
    parser.add_argument('--ticks', type=int, default=None)
    parser.add_argument('--period', type=int, default=100000)
    parser.add_argument('--name', default='practica')
    parser.add_argument('--fast', action='store_true', help='omitir espera ociosa entre precios: equivalencia funcional, no ronda con periodo fijo')
    parser.add_argument('--profile', action='store_true', help='medir ciclos e instrucciones por seccion sin modificar el programa')
    parser.add_argument('--program', type=Path, default=ROOT/'sw/trade.s', help='assembly que se ensambla y ejecuta; permite comparar con la base conservada')
    args = parser.parse_args()
    if args.edges:
        rng = random.Random(4)
        prices = [100]*30 + [101, 99] + [100]*32 + ([255]*40 + [1]*40)*3
        prices += [rng.randint(1, 255) for _ in range(512)]
    else:
        prices = read_prices(args.series)
    if args.ticks is not None:
        if not 1 <= args.ticks <= len(prices):
            parser.error('--ticks fuera de rango')
        prices = prices[:args.ticks]
    if not 1 <= len(prices) <= 100000 or args.period < 100000:
        parser.error('1..100000 ticks y periodo >=100000 ns requeridos')
    summary, rows = run(prices, 'reversion_media', official_rules(), {'ventana': 32, 'banda': 1})
    output = ROOT / 'build' / 'strategy_d' / args.name
    output.mkdir(parents=True, exist_ok=True)
    (output / 'result.json').unlink(missing_ok=True)
    reference = output / 'reference.mem'
    reference.write_text(''.join(f"{r['cash']:08x}{r['shares']:08x}{r['next_decision']:08x}{r['price']:08x}\n" for r in rows))
    program = args.program.resolve()
    program_hex = output / 'program.hex'
    subprocess.run([sys.executable, str(ROOT/'tools/assembler.py'), str(program), '-o', str(program_hex)], cwd=ROOT, check=True)
    cells = subprocess.check_output(['yosys-config', '--datdir'], text=True).strip() + '/ice40/cells_sim.v'
    executable = output / 'simulation'
    sources = sorted(ROOT.glob('rtl/*.v')) + sorted(ROOT.glob('rtl/espino_core/*.v'))
    subprocess.run(['iverilog', '-g2012', '-DNO_ICE40_DEFAULT_ASSIGNMENTS', '-s', 'tb_strategy_d', f'-Ptb_strategy_d.PROGRAM="{program_hex}"', '-o', str(executable), cells, *map(str, sources), str(ROOT / 'tb/tb_strategy_d.sv')], cwd=ROOT, check=True)
    profile_args = []
    if args.profile:
        from profile_d import prepare_profile
        prepare_profile(output, program, program_hex)
        profile_args = [f'+PROFILE={output / "profile"}', f'+PROFILE_MAP={output / "profile_map.mem"}']
    subprocess.run(['vvp', '-n', str(executable), f'+REF={reference}', f'+TICKS={len(prices)}', f'+PERIOD={args.period}', f'+FAST={int(args.fast)}', f'+METRICS={output / "metrics.csv"}', *profile_args], cwd=ROOT, check=True)
    metrics = list(csv.DictReader((output / 'metrics.csv').open()))
    cycles = [int(r['cycles']) for r in metrics]
    instructions = [int(r['instructions']) for r in metrics]
    report = dict(strategy='D', window=32, band=1, retirement_threshold=None,
                  period_ns=None if args.fast else args.period,
                  deadline_budget_period_ns=args.period, idle_wait_omitted=args.fast, expected_summary=summary,
                  program=str(program.relative_to(ROOT)) if program.is_relative_to(ROOT) else str(program),
                  hex_sha256=hashlib.sha256(program_hex.read_bytes()).hexdigest(),
                  prices_sha256=hashlib.sha256(bytes(prices)).hexdigest(),
                  metrics=dict(ticks=len(metrics), max_cycles=max(cycles), mean_cycles=sum(cycles)/len(cycles),
                               max_instructions=max(instructions), mean_instructions=sum(instructions)/len(instructions),
                               cpi_service=sum(cycles)/sum(instructions)),
                  verified='RTL, SPI, every next decision, cash and shares, deadlines')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
