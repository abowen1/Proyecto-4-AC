"""M: entrada corta por subida observada y salida por tiempo al precio siguiente.

Hipótesis de oscilación con ejecución retardada; no presupone que vaya a ganar.
No ve precios futuros. Si compra ejecuta en t, vende en t+holding; emite la
venta un tick antes de esa ejecución, incluso en el mismo tick de compra.
"""
from collections import deque

CASES={
 'M_A':dict(lookback=1,threshold=1,holding=1),
 'M_B':dict(lookback=1,threshold=2,holding=1),
 'M_C':dict(lookback=4,threshold=2,holding=4),
}
COMMON=dict(exposure_cap=50,max_quantity=63,position='One entry only; no averaging',
            entry='current_price - price_lookback_ticks_ago >= threshold, inclusive',
            exit='Fixed holding intervals from actual buy fill; sell decision one tick before execution',
            cooldown='No added cooldown; may request new entry after actual sale, executes next tick',
            protections='No TP/SL/trailing in this timing experiment',
            horizon='No ticker/date/remaining ticks or forced final sale',
            units='Thresholds in normalized integer price units, not USD or percentage')

class ShortSignal:
    def __init__(self,lookback,threshold):
        self.lookback,self.threshold=lookback,threshold
        self.prices=deque(maxlen=lookback+1)
    def observe(self,price):
        self.prices.append(price)
        if len(self.prices)<self.lookback+1:return 0
        return int(price-self.prices[0]>=self.threshold)

class FixedHolding:
    def __init__(self,holding):
        self.holding=holding;self.tick=-1;self.entry_tick=None;self.cost=0
        self.records=[];self.closed=[]
    def decide(self,signal,market,price,fill):
        self.tick+=1;fee=market.rules.commission
        if fill>0:
            assert self.entry_tick is None
            self.entry_tick=self.tick;self.cost=fill*price+fee
        elif fill<0:
            assert market.shares==0 and self.entry_tick is not None
            assert self.tick-self.entry_tick==self.holding
            self.closed.append(dict(entry_tick=self.entry_tick,exit_tick=self.tick,holding=self.holding,
                                    shares=-fill,net_profit=(-fill)*price-fee-self.cost))
            self.entry_tick=None;self.cost=0
        decision=0;reason='hold'
        if market.shares:
            if self.tick-self.entry_tick>=self.holding-1:
                decision=0x80|min(63,market.shares);reason='scheduled_exit'
        elif signal>0:
            q=min(63,max(0,(market.cash-fee)//price),max(0,50*(market.equity-fee)//(100*price)))
            if q:decision=0x40|q;reason='entry'
        self.records.append(dict(reason=reason,entry_tick=self.entry_tick,entry_cost=self.cost))
        return decision
