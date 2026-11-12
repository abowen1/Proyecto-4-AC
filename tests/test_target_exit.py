from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from backtest import Market, Rules, run
from compare_protections import Protection
from compare_target_exit import TargetExit


class TargetExitTests(unittest.TestCase):
    def test_trigger_uses_wealth_and_does_not_guarantee_cash_floor(self):
        m=Market(Rules());p=TargetExit()
        m.execute(0x7f,50)
        m.execute(0,250)
        self.assertLess(m.cash,20000)
        self.assertGreater(m.equity,20000)
        self.assertEqual(p.decide(1,m,250,0),0xbf)
        fill=m.execute(0xbf,200)
        self.assertEqual(p.decide(1,m,200,fill),0)
        self.assertLess(m.cash,20000)
        for _ in range(40):
            self.assertEqual(p.decide(1,m,50,0),0)

    def test_liquidation_requires_multiple_delayed_orders(self):
        m=Market(Rules());p=TargetExit()
        for _ in range(3):m.execute(0x7f,10)
        m.execute(0,100)
        d=p.decide(0,m,100,0)
        self.assertEqual(m.shares,189)  # observing trigger did not sell
        for expected in (126,63,0):
            self.assertEqual(d,0xbf)
            fill=m.execute(d,100)
            self.assertEqual(m.shares,expected)
            d=p.decide(1,m,100,fill)
        self.assertEqual(d,0)
        self.assertIsNotNone(p.flat)

    def test_unreached_target_matches_base_and_is_causal(self):
        prices=[100+(i*17)%31 for i in range(200)]
        for filter_on in (False,True):
            _,base=run(prices,'reversion_media',Rules(),policy=Protection('F') if filter_on else None)
            policy=TargetExit(Protection('F') if filter_on else None,target=1000000000)
            _,full=run(prices,'reversion_media',Rules(),policy=policy)
            self.assertEqual(full,base)
            _,prefix=run(prices[:100],'reversion_media',Rules(),policy=TargetExit(Protection('F') if filter_on else None,target=1000000000))
            self.assertEqual(prefix,full[:100])


if __name__=='__main__':unittest.main()
