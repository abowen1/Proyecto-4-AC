"""Cambios de entrada solamente; conserva gestión y salidas de cada padre."""
from collections import deque
from baltazar import Momentum,Management,CASES as PREVIOUS

CASES={
    'D':dict(label='Original (D)',parent='D',entry='original'),
    'Paciente_1':dict(label='Baltazar Paciente 1',parent='B6_paciente',entry='original'),
    'Paciente_2':dict(label='Baltazar Paciente 2',parent='B6_paciente',entry='trend'),
    'Lento_1':dict(label='Baltazar Lento 1',parent='B7_lento',entry='original'),
    'Lento_2':dict(label='Baltazar Lento 2',parent='B7_lento',entry='fast_timing'),
}
ENTRY_PARAMETERS=dict(short_trend_window=32,long_trend_window=128,
                      trend='SMA32>SMA128 AND current price>SMA128; strict, include current price',
                      fast_momentum_intervals=16,fast_momentum_per_mille=10,fast_confirmation=2,
                      patient2='Only adds trend gate to original momentum32>2% confirmed3 entry',
                      slow2='Replaces slow entry trigger with momentum16>1% confirmed2 AND trend gate; retains original momentum128 signal for exits',
                      risk='All risk and quantity rules inherited unchanged; entry filters never block exits')

class EntryModel:
    def __init__(self,parent):
        self.slow=Momentum(parent['intervals'],parent['threshold'],parent['confirm'])
        self.fast=Momentum(16,10,2)
        self.prices=deque(maxlen=128)
        self.trend=False;self.fast_signal=0
        self.signal=0
    def observe(self,price):
        self.signal=self.slow.observe(price)
        self.fast_signal=self.fast.observe(price)
        self.prices.append(price)
        self.trend=False
        if len(self.prices)==128:
            total=sum(self.prices);short=sum(list(self.prices)[-32:])
            self.trend=short*128>total*32 and price*128>total
        return self.signal

class EntryManagement(Management):
    def __init__(self,parent,model,mode):
        super().__init__(parent);self.model=model;self.mode=mode
    def decide(self,signal,market,price,fill):
        effective=signal
        if not market.shares:
            if self.mode=='trend':effective=signal if self.model.trend else 0
            elif self.mode=='fast_timing':effective=1 if self.model.trend and self.model.fast_signal>0 else 0
        result=super().decide(effective,market,price,fill)
        self.records[-1].update(effective_signal=effective,trend_gate=int(self.model.trend),
                                fast_signal=self.model.fast_signal)
        return result
