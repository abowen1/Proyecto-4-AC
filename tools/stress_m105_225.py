"""Secuencia artificial reproducible para invariantes aritmeticos; no backtest financiero."""
import json,random,subprocess
from backtest import ROOT
from measure_m105_225 import compile_profile,measure
from compare_m105_225_implementations import CASES

def main():
    rng=random.Random(105225)
    prices=list(range(1,256))+list(range(255,0,-1))+[rng.randint(1,255) for _ in range(1200)]
    reports=[]
    for case,(variant,p) in CASES.items():
        exe,image=compile_profile(variant,ROOT/p)
        reports.append(measure(prices,'stress1710',variant,ROOT/p,exe,image))
    assert len({r['summary']['equity'] for r in reports})==1
    (ROOT/'build/m105_225_measure/stress.json').write_text(json.dumps(dict(status='PASS',technical_only=True,seed=105225,ticks=1710,results=reports),indent=2))

if __name__=='__main__':main()
