"""Causalidad y separación entre filtros de entrada y protecciones/salidas."""
from backtest import Market,Rules
from baltazar import CASES as PREVIOUS
from generations import CASES,EntryModel,EntryManagement
from compare_generations import simulate

def main():
    prices=[100]*128+[100+i//4 for i in range(64)]
    first={}
    for name in ('Lento_1','Lento_2'):
        _,rows,_=simulate(prices,name)
        first[name]=next(i for i,r in enumerate(rows) if r['next_decision']>>6==1)
    assert first['Lento_2']<first['Lento_1'],first
    _,rows,_=simulate([100+i//8 for i in range(200)],'Paciente_2')
    assert all(r['next_decision']==0 for r in rows[:127]),'Trend requires128 samples'
    _,rows,_=simulate([200-i//2 for i in range(128)]+[137+i for i in range(24)],'Paciente_2')
    assert any(r['signal']>0 and not r['trend_gate'] and r['shares']==0 and r['next_decision']==0 for r in rows),'Rebound under slow trend must be filtered'
    for parent in ('B6_paciente','B7_lento'):
        cfg=PREVIOUS[parent];model=EntryModel(cfg);model.trend=False;model.fast_signal=1
        policy=EntryManagement(cfg,model,'fast_timing');market=Market(Rules())
        market.shares=10;market.cash=9000;market.equity=10000
        policy.decide(1,market,100,10)
        market.execute(0,80)
        assert policy.decide(-1,market,80,0)>>6==2
        assert policy.records[-1]['reason']=='stop_loss','Entry gate/min hold cannot block stop'
        policy=EntryManagement(cfg,model,'fast_timing');market=Market(Rules())
        market.shares=10;market.cash=9000;market.equity=10000
        policy.decide(1,market,100,10);policy.tick=100
        assert policy.decide(-1,market,100,0)>>6==2
        assert policy.records[-1]['reason']=='signal_exit','Fast entry must not replace original exit signal while holding'
    prices=[100]*128+[100+i//3 for i in range(150)]+[150-i//3 for i in range(150)]
    for name in CASES:
        _,full,_=simulate(prices,name)
        for n in (32,128,150,300):
            _,part,_=simulate(prices[:n],name)
            assert part==full[:n],(name,n,'Future suffix changes past')
    print('PASS: entry timing, trend warmup/rebound filter, unchanged exit signal, always-active stops and causal prefixes for all five strategies')

if __name__=='__main__':main()
