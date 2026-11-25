"""Verifica causalidad, fills con salto de precio y estado después de un stop."""
from compare_baltazar import simulate

def main():
    prices=[100]*5+[102,102,100,80]+[103,104,106,108,110,112,114,116,118,120]
    _,rows,policy=simulate(prices,'Baltazar_50_SL')
    assert rows[5]['next_decision']>>6==1 and rows[5]['shares']==0
    assert rows[6]['shares']==48 and rows[6]['entry_cost']==48*102+5
    assert rows[7]['reason']=='stop_loss' and rows[7]['shares']==48
    assert rows[8]['shares']==0 and policy.closed[0]['net_profit']==48*80-5-(48*102+5)
    assert all(r['next_decision']==0 for r in rows[8:16]),'Cooldown must follow actual exit'
    for n in [6,8,9,14]:
        _,prefix,_=simulate(prices[:n],'Baltazar_50_SL')
        assert prefix==rows[:n],'A future suffix cannot change earlier decisions'
    _,gap,_=simulate([100]*5+[102,255,255],'Baltazar_50_SL')
    assert gap[5]['next_decision']&63==48
    assert gap[6]['shares']==39 and gap[6]['entry_cost']==39*255+5,'Use actual clipped fill and execution price'
    assert gap[6]['shares']*gap[6]['price']>gap[6]['equity']/2,'Observed-price exposure cap is not a guaranteed next-price cap'
    _,tp,policy=simulate([100]*5+[102,102,106,106],'Baltazar_50_TP_SL')
    assert tp[7]['reason']=='take_profit' and tp[8]['shares']==0
    assert policy.closed[0]['net_profit']==48*(106-102)-10
    _,trail,policy=simulate([100]*5+[102,102,104,103,102,102],'Baltazar_50_trailing')
    assert trail[8]['shares']>0 and trail[9]['reason']=='trailing' and trail[10]['shares']==0
    print('PASS: delayed execution, real fill/cost, gap at stop, cooldown, causal prefix, TP and trailing')

if __name__=='__main__':main()
