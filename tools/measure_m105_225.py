"""Perfil pasivo y equivalencia de M105-225 para variantes software/hardware."""
import argparse,csv,hashlib,json,subprocess,sys,tempfile,shutil
from pathlib import Path
from backtest import ROOT,read_prices
from hardware_variants import rtl_sources
from verify_m105_225 import verify,technical_cases

ISA={'software':'base','shifter':'shifter','qcap':'qcap'}

def compile_profile(variant,program):
    out=ROOT/'build/m105_225_measure/compilers'/program.stem;out.mkdir(parents=True,exist_ok=True)
    image=out/'program.hex'
    subprocess.run([sys.executable,str(ROOT/'tools/assembler.py'),str(program),'--isa',ISA[variant],'-o',str(image)],check=True,capture_output=True,text=True)
    bench=ROOT/'tb/tb_m105_225_profile.sv';sources=rtl_sources(variant)
    cells=Path(subprocess.check_output(['yosys-config','--datdir'],text=True).strip())/'ice40/cells_sim.v'
    digest=hashlib.sha256(b''.join(p.read_bytes() for p in [image,bench,cells,*sources])).hexdigest()
    temp=Path(tempfile.gettempdir())/('ac4_m_profile_'+digest[:16]);exe=temp/'obj/simulation'
    if not exe.exists():
        temp.mkdir(exist_ok=True);staged=[]
        for p in [cells,*sources,bench]:
            dest=temp/p.name;shutil.copyfile(p,dest);staged.append(str(dest))
        shutil.copyfile(image,temp/'program.hex')
        cmd=['verilator','--binary','--timing','--top-module','tb_m105_225_profile','-Wno-fatal','-DNO_ICE40_DEFAULT_ASSIGNMENTS',f'-GPROGRAM="{temp/"program.hex"}"','--Mdir',str(temp/'obj'),'-o','simulation','-j','2',*staged]
        with (out/'compile.log').open('w') as log:subprocess.run(cmd,cwd=temp,stdout=log,stderr=subprocess.STDOUT,check=True)
    return exe,image

def pc_map(program):
    labels={};code=[]
    for line in program.read_text().splitlines():
        line=line.split('#')[0].strip()
        if line.endswith(':'):labels[line[:-1]]=len(code)*4
        elif line and not line.startswith('.'):code.append(line)
    return labels,code

def measure(prices,name,variant,program,exe,image,period=100000,fast=True):
    run_name='profile_'+program.stem+'_'+name
    result=verify(prices,run_name,exe,period,fast,program_hex=image)
    out=ROOT/'build/m105_225/runs'/run_name
    rows=list(csv.DictReader((out/'actual.csv').open()));pcs=list(csv.DictReader((out/'actual.csv.pc.csv').open()))
    cycles=[int(r['cycles']) for r in rows];ic=[int(r['instructions']) for r in rows]
    assert sum(int(p['cycles']) for p in pcs)==sum(cycles)
    assert sum(int(p['instructions']) for p in pcs)==sum(ic)
    labels,code=pc_map(program)
    # Sections use actual labels from each program, never D's SMA profile.
    boundaries=[(0,'io'),(labels['wait_price']+16,'account_control'),(labels['fill_buy'],'buy_account'),(labels['fill_sell'],'sell_account'),(labels['accounted'],'policy'),(labels['size_buy'],'size_buy'),(labels['close_accumulation'],'policy'),(labels['propose_sell'],'sell_quantity'),(labels['publish'],'io')]
    assert boundaries==sorted(boundaries)
    sections={};detailed=[]
    for row in pcs:
        pc=int(row['pc']);key=next(k for start,k in reversed(boundaries) if pc>=start)
        detail=dict(pc=pc,instruction=code[pc//4],section=key,cycles=int(row['cycles']),instructions=int(row['instructions']))
        detailed.append(detail);sections[key]=sections.get(key,0)+detail['cycles']
    peak=max(range(len(rows)),key=lambda i:cycles[i])
    metrics=dict(status='PASS',name=name,variant=variant,program=str(program.relative_to(ROOT)),ticks=len(rows),total_cycles=sum(cycles),total_instructions=sum(ic),mean_cycles=sum(cycles)/len(rows),max_cycles=max(cycles),mean_ic=sum(ic)/len(ic),max_ic=max(ic),cpi=sum(cycles)/sum(ic),mean_us=sum(cycles)/len(rows)*.04,max_us=max(cycles)*.04,service_decisions_per_second=25000000/(sum(cycles)/len(rows)),worst_tick=peak,sections=sections,pc_details=detailed,summary=result['summary'],program_sha256=result['program_sha256'],scope='25MHz response-service window(byte_done,DECISION],includes pipeline stalls; idle waiting omitted only if fast. IC counts commits,not static lines. No clock changes.')
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print('MEASURE',program.stem,name,metrics['mean_cycles'],metrics['max_cycles'],flush=True)
    return metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=list(ISA),default='software');p.add_argument('--program',type=Path,default=ROOT/'sw/trade_m105_225.s');p.add_argument('--series',type=Path);p.add_argument('--technical',action='store_true');p.add_argument('--name',default='meta');args=p.parse_args()
    program=args.program.resolve();exe,image=compile_profile(args.variant,program)
    if args.technical:
        for name,prices in technical_cases().items():measure(prices,name,args.variant,program,exe,image)
    else:measure(read_prices(args.series or ROOT/'tb/practica_meta.csv'),args.name,args.variant,program,exe,image)

if __name__=='__main__':main()
