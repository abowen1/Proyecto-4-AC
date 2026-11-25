"""Baltazar: momentum y gestión por operación, sin entradas futuras ni cambios de mercado.

Prototipo Python, no firmware. Recibe señales del backtest y lleva el costo de
una posición a partir del fill al precio recibido (reproducible localmente en
el SoC usando la orden previa y las mismas reglas de caja/inventario).
"""
from collections import deque

CASES = {
    'D': dict(model='D', original=True, description='D original, SMA32 banda1, cantidades originales'),
    'Baltazar_100': dict(model='momentum', cap=100, description='Momentum, tope100%, sin TP/SL'),
    'Baltazar_50': dict(model='momentum', cap=50, description='Momentum, tope50%, sin TP/SL'),
    'Baltazar_15': dict(model='momentum', cap=15, description='Momentum, tope15%, sin TP/SL'),
    'Baltazar_50_SL': dict(model='momentum', cap=50, sl=15, description='Momentum50%, SL neto1.5%'),
    'Baltazar_50_TP_SL': dict(model='momentum', cap=50, tp=15, sl=15, description='Momentum50%, TP neto1.5%, SL neto1.5%'),
    'Baltazar_50_trailing': dict(model='momentum', cap=50, sl=15, trailing=15, activate=15, description='Momentum50%, SL neto1.5%; trailing1.5% tras alcanzar ganancia neta1.5%'),
    'D_gestion_Baltazar': dict(model='D', cap=50, tp=15, sl=15, description='Entrada/salida D con gestión Baltazar: una posición,50%,TP/SL1.5%,espera8'),
}

COMMON = dict(momentum_intervals=5, momentum_per_mille=8, cooldown_ticks=8,
              position='one buy order per position, no adding until flat',
              quantity='integer, maximum63, clipped by actual funds next tick',
              exposure='cap limits new entry at observed price after estimated buy fee; no forced rebalancing',
              exit='opposite momentum (or D sell), stop, take profit or activated trailing; whichever occurs first',
              return_basis='net liquidation value shares*price minus sell fee, versus actual entry cost including buy fee',
              stop_execution='decision now executes next price, no guarantee at threshold',
              horizon='no ticker/date/remaining ticks/end-of-series inputs; no forced final liquidation')

class Momentum:
    def __init__(self, intervals=5, threshold=8):
        self.prices=deque(maxlen=intervals+1)
        self.intervals,self.threshold=intervals,threshold
    def observe(self,price):
        self.prices.append(price)
        if len(self.prices)<self.intervals+1:return 0
        old=self.prices[0];change=(price-old)*1000
        return 1 if change>self.threshold*old else -1 if change<-self.threshold*old else 0

class Management:
    def __init__(self,config):
        self.config=config
        self.tick=-1;self.blocked_until=0
        self.cost=0;self.peak_net=0
        self.closing_reason=None
        self.records=[]
        self.closed=[]
        self.bought=None

    def decide(self,signal,market,price,fill):
        self.tick+=1;fee=market.rules.commission
        if fill>0:
            assert self.cost==0,'No averaging or concurrent entry allowed'
            self.cost=fill*price+fee
            self.peak_net=fill*price-fee
            self.bought=self.tick
        elif fill<0:
            assert market.shares==0,'Single entry is at most63; exit must close it'
            self.closed.append(dict(entry_tick=self.bought,exit_tick=self.tick,
                                    net_profit=(-fill)*price-fee-self.cost,
                                    reason=self.closing_reason or 'signal'))
            self.cost=self.peak_net=0;self.closing_reason=None;self.bought=None
            self.blocked_until=self.tick+COMMON['cooldown_ticks']

        reason='hold';decision=0
        if market.shares:
            assert self.cost>0
            net=market.shares*price-fee
            self.peak_net=max(self.peak_net,net)
            if self.closing_reason:reason=self.closing_reason
            elif self.config.get('sl') and net*1000<=self.cost*(1000-self.config['sl']):reason='stop_loss'
            elif self.config.get('tp') and net*1000>=self.cost*(1000+self.config['tp']):reason='take_profit'
            elif (self.config.get('trailing') and self.peak_net*1000>=self.cost*(1000+self.config['activate'])
                  and net*1000<=self.peak_net*(1000-self.config['trailing'])):reason='trailing'
            elif signal<0:reason='signal_exit'
            if reason!='hold':
                self.closing_reason=reason
                decision=0x80|min(63,market.shares)
        elif self.tick<self.blocked_until:reason='cooldown'
        elif signal>0:
            q=min(63,max(0,(market.cash-fee)//price),
                  max(0,self.config['cap']*(market.equity-fee)//(100*price)))
            if q:decision=0x40|q;reason='entry'
        self.records.append(dict(reason=reason,entry_cost=self.cost,
                                 peak_net=self.peak_net,blocked_until=self.blocked_until))
        return decision
