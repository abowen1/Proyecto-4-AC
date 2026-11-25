"""Pruebas de ejecución, confirmación, espera y protecciones sin información futura."""
from backtest import run,official_rules
from baltazar import Momentum,Management,CASES
from compare_baltazar import simulate

def custom(prices,**changes):
    cfg=dict(cap=50,tp=15,sl=15);cfg.update(changes)
    policy=Management(cfg)
    summary,rows=run(prices,'reversion_media',official_rules(),dict(ventana=32,banda=1),policy,signal_model=Momentum())
    return rows,policy

def main():
    prices=[100]*5+[102,102,100,80]+[110]*80
    rows,policy=custom(prices,cooldown=64,min_hold=64)
    assert rows[5]['next_decision']>>6==1 and rows[5]['shares']==0
    assert rows[6]['shares']==48
    assert policy.records[6]['entry_cost']==48*102+5
    assert policy.records[7]['reason']=='stop_loss', 'Min holding time must not block protective stop'
    assert rows[8]['shares']==0
    assert policy.closed[0]['net_profit']==48*80-5-(48*102+5), 'Stop must execute at next actual price'
    assert all(r['next_decision']==0 for r in rows[8:72]), '64 tick cooldown begins at actual sale'
    gap,pol=custom([100]*5+[102,255,255])
    assert gap[5]['next_decision']&63==48 and gap[6]['shares']==39
    assert pol.records[6]['entry_cost']==39*255+5
    m=Momentum(2,10,3)
    assert [m.observe(p) for p in [100,100,102,103,104]]==[0,0,0,0,1]
    m=Momentum(1,10,1);assert m.observe(100)==0 and m.observe(101)==0
    rows,pol=custom([100]*5+[102,102,100,100],tp=40,sl=30,exit_on_signal=False)
    assert all(r['next_decision']==0 for r in rows[6:]), 'No signal exit when disabled'
    rows,pol=custom([100]*5+[102,102,104,103,102,102],tp=None,trailing=15,activate=15)
    assert pol.records[9]['reason']=='trailing' and rows[10]['shares']==0
    long_prices=[100]*8+[100+i//4 for i in range(256)]+[164-i//3 for i in range(200)]
    for name in CASES:
        _,full,_=simulate(long_prices,name)
        for n in [8,36,140,300]:
            _,prefix,_=simulate(long_prices[:n],name)
            assert prefix==full[:n], (name,n,'Future suffix changed past decisions')
    print('PASS: confirmed signals, delayed actual fills, gap stops, stop bypasses minimum hold, cooldown64, exit suppression, trailing and causal prefixes for all nine cases')

if __name__=='__main__':main()
