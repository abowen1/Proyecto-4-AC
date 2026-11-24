"""Equivalencia M105-225: instrucciones base, SoC y SPI; sin sintesis ni placa."""
import argparse, csv, hashlib, json, re, subprocess, sys, time, tempfile, shutil
from pathlib import Path
from backtest import ROOT, read_prices
from hardware_variants import rtl_sources
from m105_225 import simulate

STATES={'flat':0,'buying':1,'holding':2,'selling':3}

def technical_cases():
    return {
        'thresholds':[106,105,104,106,104,224,225,224,226,105,100,225,100,100,100,225,225],
        'gaps_and_latched_exit':[105,255,100,100,225,1,1,255,105,255,225,100,225,225],
        'no_averaging_after_band':[105,106,100,100,100,224,225,224,100,100,100,225,224,100],
        'budget_and_partial_fills':[100]*8+[225]*6+[1]*160+[255]+[1]*164+[255]*164,
        'no_final_sale':[100]*10,
    }

def assemble():
    output=ROOT/'build/m105_225';output.mkdir(parents=True,exist_ok=True)
    image=output/'program.hex'
    subprocess.run([sys.executable,str(ROOT/'tools/assembler.py'),str(ROOT/'sw/trade_m105_225.s'),'-o',str(image)],check=True,capture_output=True,text=True)
    return output,image

def compile_simulator(engine):
    output,image=assemble();sources=rtl_sources('software');bench=ROOT/'tb/tb_m105_225.sv'
    cells=Path(subprocess.check_output(['yosys-config','--datdir'],text=True).strip())/'ice40/cells_sim.v'
    stamp=hashlib.sha256(b''.join(p.read_bytes() for p in [image,bench,*sources])+engine.encode()).hexdigest()
    dest=output/engine;dest.mkdir(exist_ok=True)
    temp=Path(tempfile.gettempdir())/('ac4_m105_225_'+stamp[:16])
    executable=dest/'simulation' if engine=='iverilog' else temp/'obj/simulation'
    signature=dest/'signature.txt'
    if executable.exists() and signature.exists() and signature.read_text()==stamp:return executable
    if engine=='iverilog':
        command=['iverilog','-g2012','-DNO_ICE40_DEFAULT_ASSIGNMENTS','-s','tb_m105_225',f'-Ptb_m105_225.PROGRAM="{image}"','-o',str(executable),str(cells),*map(str,sources),str(bench)]
    else:
        # GNU Make/Verilator no admite carpetas con espacios. Copias byte-identicas.
        temp.mkdir(parents=True,exist_ok=True)
        staged=[]
        for source in (cells,*sources,bench):
            target=temp/source.name;shutil.copyfile(source,target);staged.append(str(target))
        shutil.copyfile(image,temp/'program.hex')
        command=['verilator','--binary','--timing','--top-module','tb_m105_225','-Wno-fatal','-DNO_ICE40_DEFAULT_ASSIGNMENTS',f'-GPROGRAM="{temp/"program.hex"}"','--Mdir',str(temp/'obj'),'-o','simulation','-j','2',*staged]
    with (dest/'compile.log').open('w') as log:subprocess.run(command,cwd=(temp if engine=='verilator' else ROOT),stdout=log,stderr=subprocess.STDOUT,check=True)
    signature.write_text(stamp);return executable

def verify(prices,name,executable,period=100000,fast=True):
    summary,rows,policy=simulate(prices)
    out=ROOT/'build/m105_225/runs'/name;out.mkdir(parents=True,exist_ok=True)
    result=out/'result.json';result.unlink(missing_ok=True)
    ref=out/'reference.mem'
    ref.write_text(''.join(''.join(f'{v&0xffffffff:08x}' for v in (STATES[r['state']],r['episode_budget']-r['acquisition_cost'],r['cash'],r['shares'],r['next_decision'],r['price']))+'\n' for r in rows))
    command=[str(executable),f'+REF={ref}',f'+OUT={out/"actual.csv"}',f'+TICKS={len(prices)}',f'+PERIOD={period}',f'+FAST={int(fast)}']
    if executable.parent.name=='iverilog':command=['vvp','-n',*command]
    with (out/'simulation.log').open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    text=(out/'simulation.log').read_text();assert 'PASS M105-225:' in text
    # Independent replay of actual emitted decisions verifies downstream accounting too.
    from backtest import Market,official_rules
    market=Market(official_rules());previous=0;actual=list(csv.DictReader((out/'actual.csv').open()))
    assert len(actual)==len(rows)
    for a,r in zip(actual,rows):
        market.execute(previous,int(a['price']))
        for k in ('tick','price','next_decision','cash','shares'):assert int(a[k])==r[k],(name,r['tick'],k)
        assert market.cash==r['cash'] and market.shares==r['shares'] and market.equity==r['equity']
        assert market.orders==r['orders'] and market.orders*5==r['commissions'] and market.max_dd==r['max_drawdown']
        previous=int(a['next_decision'])
    report=dict(status='PASS',strategy='M105-225',ticks=len(rows),summary=summary,engine='iverilog' if executable.parent.name=='iverilog' else 'verilator',fixed_period_ns=None if fast else period,
        deadline_period_ns=period,program_sha256=hashlib.sha256((ROOT/'build/m105_225/program.hex').read_bytes()).hexdigest(),price_bytes_sha256=hashlib.sha256(bytes(prices)).hexdigest(),
        verified='SoC RTL,physical SPI protocol in simulation,every next decision,cash,shares,policy state,remaining budget;actual decisions replayed for equity,orders,fees,drawdown',
        scope='Simulation only. Deadline is a safety check; no performance profile,optimization,FPGA bitstream or physical programming.')
    result.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',name,len(rows),summary['equity'],flush=True);return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=['iverilog','verilator'],default='iverilog')
    parser.add_argument('--series',type=Path);parser.add_argument('--ticks',type=int)
    parser.add_argument('--technical',action='store_true');parser.add_argument('--fixed',action='store_true')
    parser.add_argument('--period',type=int,choices=[100000,1000000,10000000],default=100000)
    parser.add_argument('--name',default='single');args=parser.parse_args()
    exe=compile_simulator(args.engine)
    if args.technical:
        for name,prices in technical_cases().items():verify(prices,name+'_'+args.engine+('_fixed_'+str(args.period) if args.fixed else ''),exe,args.period,not args.fixed)
    elif args.series:
        prices=read_prices(args.series)
        if args.ticks:prices=prices[:args.ticks]
        verify(prices,args.name,exe,args.period,not args.fixed)
    else:parser.error('Usar --technical o --series')

if __name__=='__main__':main()
