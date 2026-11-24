"""M105-225 en Espino base: testbench oficial conservando contabilidad y SPI."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import shutil

from backtest import ROOT, official_rules, read_prices, run
from hardware_variants import rtl_sources
from m105_225 import simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--series', type=Path, default=ROOT/'tb/practica_meta.csv')
    parser.add_argument('--ticks', type=int, default=2000)
    parser.add_argument('--period', type=int, choices=(100000, 1000000, 10000000), default=100000)
    parser.add_argument('--engine',choices=['iverilog','verilator'],default='iverilog')
    args = parser.parse_args()
    prices = read_prices(args.series)
    if not 1 <= args.ticks <= len(prices):
        parser.error('Cantidad de precios fuera de la serie disponible')
    output = ROOT/'build/canvas_m105_225'/args.series.stem/f'{args.ticks}_{args.period}_{args.engine}'
    output.mkdir(parents=True, exist_ok=True)
    (output/'result.json').unlink(missing_ok=True)
    image = output/'program.hex'
    subprocess.run([sys.executable, str(ROOT/'tools/assembler.py'),
                    str(ROOT/'sw/trade_m105_225.s'), '--isa', 'base', '-o', str(image)], check=True)
    original = ROOT/'tb/tb_proyecto_4.sv'
    bench = original.read_text()
    # Icarus no admite localparam string; quitar el tipo no cambia su valor.
    bench = bench.replace('localparam string', 'localparam')
    for name, value in [('PROGRAMA', f'"{image}"'), ('SERIE', f'"{args.series.resolve()}"'),
                        ('NTICKS', str(args.ticks)), ('PERIODO_NS', str(args.period))]:
        bench, count = re.subn(r'(localparam\s+(?:int\s+)?'+name+r'\s*=\s*)[^;]+;',
                               lambda m: m[1]+value+';', bench)
        if count != 1:
            raise ValueError(f'Parámetro de Canvas ausente o ambiguo: {name}')
    # Únicamente rutas/parámetros/tipado: SPI, contabilidad y chequeos intactos.
    bench_path = output/'tb_canvas_configurado.sv'
    bench_path.write_text(bench)
    cells = subprocess.check_output(['yosys-config', '--datdir'], text=True).strip()+'/ice40/cells_sim.v'
    executable = output/'simulation'
    if args.engine=='iverilog':
        subprocess.run(['iverilog','-g2012','-DNO_ICE40_DEFAULT_ASSIGNMENTS','-s','tb_proyecto_4','-o',str(executable),cells,*map(str,rtl_sources('software')),str(bench_path)],check=True,capture_output=True,text=True)
        command=['vvp','-n',str(executable)]
    else:
        # Copias byte-identicas, para evitar espacios en el directorio de GNU Make.
        temp=Path(tempfile.mkdtemp(prefix='ac4_canvas_m105_225_'))
        staged=[]
        for source in [Path(cells),*rtl_sources('software'),bench_path]:
            target=temp/source.name;shutil.copyfile(source,target);staged.append(str(target))
        with (output/'compile.txt').open('w') as log:
            subprocess.run(['verilator','--binary','--timing','--top-module','tb_proyecto_4','-Wno-fatal','-DNO_ICE40_DEFAULT_ASSIGNMENTS','--Mdir',str(temp/'obj'),'-o','simulation','-j','2',*staged],cwd=temp,stdout=log,stderr=subprocess.STDOUT,check=True)
        command=[str(temp/'obj/simulation')]
    with (output/'ejecucion.txt').open('w') as log:
        subprocess.run(command,cwd=output,stdout=log,stderr=subprocess.STDOUT,check=True)
    log = (output/'ejecucion.txt').read_text()
    if 'Testbenchs aprobados: 4/4' not in log or re.search(r'\b(?:FAIL|ERROR)\b', log):
        raise AssertionError(log)
    summary, expected, _ = simulate(prices[:args.ticks])
    with (output/'decisiones.csv').open() as f:
        actual = list(csv.DictReader(f))
    if len(actual) != len(expected):
        raise AssertionError('Cantidad incorrecta de filas')
    for a, b in zip(actual, expected):
        pairs = [('tick', 'tick'), ('precio', 'price'), ('caja', 'cash'), ('acciones', 'shares'), ('patrimonio', 'equity')]
        if any(int(a[k]) != b[v] for k, v in pairs) or int(a['decision'], 16) != b['applied_decision']:
            raise AssertionError(f'Diferencia en tick {b["tick"]}: {a} vs {b}')
    result = dict(status='PASS', engine=args.engine, variant='software', strategy='M105-225', ticks=args.ticks, period_ns=args.period,
                  series=str(args.series), series_csv_sha256=hashlib.sha256(args.series.read_bytes()).hexdigest(),
                  canvas_checks='4/4', every_applied_decision_and_accounting_match=True,
                  original_testbench_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                  program_hex_sha256=hashlib.sha256(image.read_bytes()).hexdigest(), expected_summary=summary,
                  scope='Simulación de la maestra Canvas y del SoC; no señales físicas USB/SPI')
    (output/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(log.strip(), flush=True)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
