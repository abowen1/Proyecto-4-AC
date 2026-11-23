"""Comprueba acumulación y salida de varias órdenes, caja y decisiones causales."""
from compare_bands import simulate
from m_bands import CASES

def main():
    prices=[150,120,100,100,150,210,210,210,180,150,200]
    summary,rows,policy=simulate(prices,'M1')
    assert rows[1]['shares']==0 and rows[1]['next_decision']>>6==1
    assert rows[2]['shares']==63 and rows[2]['next_decision']&63==36
    assert rows[3]['shares']==99
    assert rows[6]['shares']==36 and rows[6]['next_decision']>>6==2
    assert rows[7]['shares']==0 and summary['equity']==20870
    assert summary['orders']==4 and policy.closed[0]['net_profit']==10870
    assert all(r['equity']==20870 and r['next_decision']==0 for r in rows[7:]),'Flat cash despite price movement'
    summary,rows,policy=simulate([100,100,100,210,210,210],'M2')
    assert summary['equity']==15380 and summary['orders']==2
    summary,rows,policy=simulate([100,100,100,210,205,200],'M1')
    assert rows[-1]['shares']==0 and policy.closed[0]['sell_orders']==2,'Liquidation remains latched below threshold'
    summary,rows,policy=simulate([120,130,110,110,110],'M1')
    assert rows[1]['shares']==63 and all(r['next_decision']==0 for r in rows[1:]),'Do not add after leaving entry band'
    summary,rows,policy=simulate([100,100,100],'M1')
    assert summary['shares']==99 and summary['orders']==2,'No final forced sale'
    long_prices=[200]*8+[150-i//3 for i in range(150)]+[100+i//2 for i in range(256)]+[228-i//2 for i in range(100)]
    for name in CASES:
        _,full,_=simulate(long_prices,name)
        for n in [12,100,200,400]:
            _,prefix,_=simulate(long_prices[:n],name);assert prefix==full[:n],(name,n)
    print('PASS: delayed fills, multi-order entry/exit, exposure50/100, per-order fees, flat plateaus, latched exit, no repeated averaging, no forced end sale and causal prefixes')

if __name__=='__main__':main()
