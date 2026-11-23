"""Prueba la aritmética temporal de un giro completo y ausencia de datos futuros."""
from compare_m import simulate
from m import CASES

def main():
    summary,rows,policy=simulate([100,101,100,101],'M_A')
    assert rows[1]['shares']==0 and rows[1]['next_decision']>>6==1
    assert rows[2]['shares']==49 and rows[2]['next_decision']>>6==2
    assert rows[3]['shares']==0 and summary['equity']==10039
    assert policy.closed[0]['net_profit']==39 and policy.closed[0]['holding']==1
    summary,rows,policy=simulate([100,101,255,254],'M_A')
    assert rows[2]['shares']==39 and policy.closed[0]['net_profit']==-49
    summary,rows,policy=simulate([100,100,100,100,102,102,102,102,102,102],'M_C')
    assert policy.closed[0]['entry_tick']==5 and policy.closed[0]['exit_tick']==9
    assert policy.closed[0]['net_profit']==-10
    _,rows,_=simulate([100,101,100],'M_A');assert rows[-1]['shares']==49,'Do not force final sale'
    prices=[100+i%4 for i in range(140)]+[140-i//4 for i in range(140)]
    for n in CASES:
        _,full,_=simulate(prices,n)
        for k in (3,8,40,180):
            _,prefix,_=simulate(prices[:k],n);assert prefix==full[:k],(n,k)
    print('PASS: next-price entry/sale, exact holding1/4, commission10 per roundtrip, actual clipping, no forced end sale, causal prefixes')

if __name__=='__main__':main()
