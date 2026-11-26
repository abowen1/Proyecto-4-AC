"""Genera la imagen elegida de M105-225; nunca programa la FPGA."""
import hashlib,json,shutil
from pathlib import Path
from backtest import ROOT
from assembler import assemble
from hardware_variants import build,rtl_sources

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    choice=json.loads((ROOT/'docs/estrategia/M105_225_optimizacion/seleccion_hardware.json').read_text())
    comparison_path=ROOT/'build/m105_225_measure/comparison.json'
    if not comparison_path.exists():comparison_path=ROOT/'docs/estrategia/M105_225_optimizacion/validacion_variantes.json'
    comparison=json.loads(comparison_path.read_text())
    assert comparison['status']=='PASS'
    program=ROOT/choice['program'];measured=ROOT/choice['measured_program']
    assert assemble(program.read_text(),isa=choice['isa'])==assemble(measured.read_text(),isa=choice['isa'])
    expected_hex=''.join(f'{w:08x}\n' for w in assemble(measured.read_text(),isa=choice['isa'])).encode()
    expected_hash=hashlib.sha256(expected_hex).hexdigest()
    proofs=[r for r in comparison['results'] if r['case']==choice['case']]
    assert len(proofs)==78 and all(r['program_sha256']==expected_hash for r in proofs)
    build(choice['variant'],choice['program'],'M105_225_final')
    source=ROOT/'build/hardware/M105_225_final'
    assert digest(source/'program.hex')==expected_hash
    result=json.loads((source/'result.json').read_text())
    assert all(v['achieved']>=25 for v in result['fmax'].values())
    assert all(v['used']<=v['available'] for v in result['utilization'].values())
    out=ROOT/'build/final';out.mkdir(exist_ok=True)
    shutil.copyfile(source/'soc.bin',out/'M105_225.bin')
    manifest=dict(status='PASS',strategy='M105-225',variant=choice['variant'],program=choice['program'],clock_hz=25000000,
                  program_hex_sha256=digest(source/'program.hex'),bitstream_sha256=digest(out/'M105_225.bin'),image_bytes=(out/'M105_225.bin').stat().st_size,
                  fmax=result['fmax'],utilization=result['utilization'],assembly_sha256=digest(program),
                  rtl_sha256={str(p.relative_to(ROOT)):digest(p) for p in rtl_sources(choice['variant'])},
                  validation='Same machine code as78 complete RTL equivalence/profile runs; synthesis and place-and-route meet25MHz',
                  physical_programming=False,physical_validation=False)
    (out/'M105_225.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest),flush=True)

if __name__=='__main__':main()
