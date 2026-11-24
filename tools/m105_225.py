"""M X-Y: bandas absolutas con memoria y liquidación completa enclavada."""
CASES={'M105-225':dict(buy=105,sell=225,exposure=100)}

COMMON=dict(buy='price<=buy threshold; inclusive',sell='price>=sell threshold; inclusive',
    allocation='Fixed episode budget exposure% of equity observed at first entry signal; includes buy fees',
    accumulation='While still inside buy band, buy remaining budget in orders<=63; stop adding once outside band or budget exhausted',
    liquidation='Latch sell after first exit signal and drain inventory in orders<=63 even if price leaves exit band',
    reentry='After flat, wait until price<=buy threshold again; no added cooldown',
    execution='Every request executes next tick; price gaps may exceed the observed-price budget',
    horizon='No date/ticker/future values, no end-of-series sale, no retirement threshold',
    risk='No separate stop/trailing/TP based on profit; exit is absolute normalized price band')

class PriceSignal:
    def __init__(self,cfg):self.cfg=cfg
    def observe(self,price):
        return 1 if price<=self.cfg['buy'] else -1 if price>=self.cfg['sell'] else 0

class BandPolicy:
    def __init__(self,cfg):
        self.cfg=cfg;self.state='flat';self.budget=0;self.spent=0;self.tick=-1
        self.proceeds=0;self.entry_tick=None;self.buy_orders=self.sell_orders=0
        self.records=[];self.closed=[]
    def decide(self,signal,market,price,fill):
        self.tick+=1;fee=market.rules.commission
        if fill>0:
            self.spent+=fill*price+fee;self.buy_orders+=1
            if self.entry_tick is None:self.entry_tick=self.tick
        elif fill<0:
            self.proceeds+=(-fill)*price-fee;self.sell_orders+=1
            if market.shares==0:
                self.closed.append(dict(entry_tick=self.entry_tick,exit_tick=self.tick,net_profit=self.proceeds-self.spent,
                                        acquisition_cost=self.spent,sale_proceeds=self.proceeds,buy_orders=self.buy_orders,sell_orders=self.sell_orders))
                self.state='flat';self.budget=self.spent=self.proceeds=0
                self.entry_tick=None;self.buy_orders=self.sell_orders=0
        if market.shares and signal<0:self.state='selling'
        if self.state=='flat' and signal>0:
            self.budget=self.cfg['exposure']*market.equity//100
            self.spent=self.proceeds=0;self.state='buying'
        decision=0;reason='hold'
        if self.state=='selling':
            if market.shares:decision=0x80|min(63,market.shares);reason='liquidate'
        elif self.state=='buying':
            if signal<=0:self.state='holding' if market.shares else 'flat'
            else:
                q=min(63,max(0,(market.cash-fee)//price),max(0,(self.budget-self.spent-fee)//price))
                if q:decision=0x40|q;reason='accumulate'
                else:self.state='holding' if market.shares else 'flat'
        self.records.append(dict(state=self.state,reason=reason,episode_budget=self.budget,acquisition_cost=self.spent))
        return decision


def simulate(prices):
    from backtest import run, official_rules
    cfg=CASES['M105-225']; policy=BandPolicy(cfg)
    summary,rows=run(prices,'mantener',official_rules(),policy=policy,signal_model=PriceSignal(cfg))
    peak=10000;dd=0
    for row,record in zip(rows,policy.records):
        peak=max(peak,row['equity']);dd=max(dd,(peak-row['equity'])/peak)
        row.update(record)
    summary.update(strategy='M105-225',label='M105-225',buy=105,sell=225,exposure=100,drawdown_percent=100*dd,closed_episodes=len(policy.closed))
    return summary,rows,policy
