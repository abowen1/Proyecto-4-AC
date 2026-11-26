"""Tres periodos reales de SPI y maestra oficial; sin hardware nuevo."""
import csv,json,subprocess,sys
from backtest import ROOT
from verify_m105_225 import compile_simulator,verify,technical_cases

def main():
    out=ROOT/'build/m105_225/integration';out.mkdir(parents=True,exist_ok=True)
    cases=technical_cases();prices=cases['thresholds']+cases['gaps_and_latched_exit']+cases['no_averaging_after_band']+[100]*3
    sequence=out/'transacciones.csv'
    with sequence.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['tick','price']);w.writerows(enumerate(prices))
    exe=compile_simulator('verilator');results=[]
    for period in (100000,1000000,10000000):
        results.append(verify(prices,'integration_'+str(period),exe,period,False))
        command=[sys.executable,str(ROOT/'tools/verify_canvas_m105_225.py'),'--series',str(sequence),'--ticks',str(len(prices)),'--period',str(period),'--engine','verilator']
        with (out/f'canvas_{period}.log').open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        source=ROOT/'build/canvas_m105_225/transacciones'/f'{len(prices)}_{period}_verilator/result.json'
        result=json.loads(source.read_text());assert result['canvas_checks']=='4/4';results.append(result)
        print('PASS: maestra oficial,periodo',period,flush=True)
    report=dict(status='PASS',strategy='M105-225',fixed_periods_ns=[100000,1000000,10000000],ticks_per_round=len(prices),rounds=6,results=results,
                scope='Fixed real-time periods in simulated SoC and official master; clocks25MHz and SPI1MHz. No FPGA bitstream or hardware modification.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
