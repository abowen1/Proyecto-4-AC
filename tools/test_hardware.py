"""Pruebas unitarias RTL y de instrucciones dentro del SoC real."""
from pathlib import Path
import subprocess
import sys
from hardware_variants import ROOT, VARIANTS, rtl_sources


def main():
    output=ROOT/'build/hardware/tests';output.mkdir(parents=True,exist_ok=True)
    cells=Path(subprocess.check_output(['yosys-config','--datdir'],text=True).strip())/'ice40/cells_sim.v'
    for variant in ('shifter','qcap'):
        unit='tb_'+variant+'_unit'
        extra=[ROOT/'variants'/variant/'rtl'/('espino_alu.v' if variant=='shifter' else 'espino_qcap.v')]
        if variant=='shifter':extra.append(ROOT/'variants/shifter/rtl/espino_decoder.v')
        subprocess.run(['iverilog','-g2012','-s',unit,'-o',str(output/variant),*map(str,extra),str(ROOT/'tb'/(unit+'.sv'))],check=True,cwd=ROOT)
        with (output/(variant+'.txt')).open('w') as f:subprocess.run(['vvp','-n',str(output/variant)],check=True,cwd=ROOT,stdout=f)
        image=output/(variant+'_diagnostic.hex')
        subprocess.run([sys.executable,'tools/assembler.py',f'sw/{variant}_diagnostic.s','--isa',VARIANTS[variant]['isa'],'-o',str(image)],check=True,cwd=ROOT)
        executable=output/(variant+'_cpu')
        define=['-DTEST_SHIFTER'] if variant=='shifter' else []
        subprocess.run(['iverilog','-g2012','-DNO_ICE40_DEFAULT_ASSIGNMENTS',*define,'-s','tb_hw_instructions',f'-Ptb_hw_instructions.PROGRAM="{image}"','-o',str(executable),str(cells),*map(str,rtl_sources(variant)),str(ROOT/'tb/tb_hw_instructions.sv')],check=True,cwd=ROOT)
        with (output/(variant+'_cpu.txt')).open('w') as f:subprocess.run(['vvp','-n',str(executable)],check=True,cwd=ROOT,stdout=f)
        print((output/(variant+'.txt')).read_text()+(output/(variant+'_cpu.txt')).read_text(),flush=True)


if __name__=='__main__':main()
