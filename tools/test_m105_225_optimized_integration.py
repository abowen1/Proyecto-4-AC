"""Control de estados y SPI de las variantes optimizadas; sin programar placa."""
import argparse,csv,json,subprocess,sys
from pathlib import Path
from backtest import ROOT
from hardware_variants import rtl_sources
from compare_m105_225_implementations import CASES
from measure_m105_225 import compile_profile,measure
from verify_m105_225 import technical_cases

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['soft','shifter','qcap'],default='soft');p.add_argument('--fixed',action='store_true');args=p.parse_args()
    variant,file=CASES[args.case];program=ROOT/file;exe,image=compile_profile(variant,program)
    cells=Path(subprocess.check_output(['yosys-config','--datdir'],text=True).strip())/'ice40/cells_sim.v'
    out=ROOT/'build/m105_225_measure/integration'/args.case;out.mkdir(parents=True,exist_ok=True)
    idir=out/'iverilog';idir.mkdir(exist_ok=True);iexe=idir/'simulation'
    subprocess.run(['iverilog','-g2012','-DNO_ICE40_DEFAULT_ASSIGNMENTS','-s','tb_m105_225_profile',f'-Ptb_m105_225_profile.PROGRAM="{image}"','-o',str(iexe),str(cells),*map(str,rtl_sources(variant)),str(ROOT/'tb/tb_m105_225_profile.sv')],cwd=ROOT,check=True,capture_output=True,text=True)
    results=[]
    for name,prices in technical_cases().items():results.append(measure(prices,name+'_iverilog',variant,program,iexe,image))
    if args.fixed:
        cases=technical_cases();prices=cases['thresholds']+cases['gaps_and_latched_exit']+cases['no_averaging_after_band']+[100]*3
        series=out/'transacciones.csv'
        with series.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['tick','price']);w.writerows(enumerate(prices))
        for period in (100000,1000000,10000000):
            results.append(measure(prices,'fixed_'+str(period),variant,program,exe,image,period,False))
            cmd=[sys.executable,str(ROOT/'tools/verify_canvas_m105_225.py'),'--variant',variant,'--program',str(program),'--series',str(series),'--ticks',str(len(prices)),'--period',str(period),'--engine','verilator']
            with (out/f'canvas_{period}.txt').open('w') as log:subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            path=ROOT/'build/canvas_m105_225_variants'/variant/program.stem/'transacciones'/f'{len(prices)}_{period}_verilator/result.json'
            results.append(json.loads(path.read_text()))
    (out/'result.json').write_text(json.dumps(dict(status='PASS',case=args.case,results=results),indent=2)+'\n')

if __name__=='__main__':main()
