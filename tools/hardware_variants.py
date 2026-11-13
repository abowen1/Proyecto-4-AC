"""Fuentes, ensamblado y compilacion aislada de las alternativas de hardware AC4."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
VARIANTS={
    'software': dict(isa='base',program='sw/trade.s'),
    'shifter': dict(isa='shifter',program='sw/trade_shifter.s'),
    'qcap': dict(isa='qcap',program='sw/trade_qcap.s'),
}


def rtl_sources(variant):
    base=sorted(ROOT.glob('rtl/*.v'))+sorted(ROOT.glob('rtl/espino_core/*.v'))
    overrides=sorted((ROOT/'variants'/('shifter' if variant=='shifter_trace' else variant)/'rtl').glob('*.v'))
    if variant=='shifter_trace':overrides+=sorted((ROOT/'variants/shifter_trace/rtl').glob('*.v'))
    replacement={p.name:p for p in overrides}
    sources=[replacement.pop(p.name,p) for p in base]+list(replacement.values())
    if len({p.name for p in sources})!=len(sources):raise ValueError('Modulo RTL duplicado')
    return sources


def build(variant, program=None, name=None):
    config=VARIANTS['shifter' if variant=='shifter_trace' else variant];output=ROOT/'build/hardware'/(name or variant)
    output.mkdir(parents=True,exist_ok=True)
    image=output/'program.hex'
    def run(command,log):
        with (output/log).open('w') as f:
            subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    run([sys.executable,'tools/assembler.py',program or config['program'],'--isa',config['isa'],'-o',str(image)],'assemble.txt')
    src=' '.join(str(p.relative_to(ROOT)) for p in rtl_sources(variant))
    prefix=output.relative_to(ROOT)
    script=f'read_verilog {src}; chparam -set MemFile "{image.relative_to(ROOT)}" pochoco_soc; synth_ice40 -top pochoco_soc -json {prefix}/soc.json; stat'
    run(['yosys','-p',script],'synthesis.txt')
    run(['nextpnr-ice40','--hx1k','--package','vq100','--json',str(output/'soc.json'),'--pcf','goboard.pcf','--asc',str(output/'soc.asc'),'--freq','25','--report',str(output/'timing.json')],'place_route.txt')
    run(['icepack',str(output/'soc.asc'),str(output/'soc.bin')],'icepack.txt')
    timing=json.loads((output/'timing.json').read_text())
    report=dict(variant=variant,program=program or config['program'],clock_hz=25000000,fmax=timing['fmax'],utilization=timing['utilization'],image_bytes=(output/'soc.bin').stat().st_size)
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant',choices=list(VARIANTS)+['shifter_trace'])
    parser.add_argument('--program');parser.add_argument('--name');args=parser.parse_args()
    build(args.variant,args.program,args.name)
