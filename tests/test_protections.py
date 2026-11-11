from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from backtest import Market, Rules, run
from compare_protections import Protection


class ProtectionTests(unittest.TestCase):
    def test_panic_liquidates_in_chunks_and_waits_before_reentry(self):
        m=Market(Rules());p=Protection('P')
        fill=m.execute(0x7f,60);p.decide(0,m,60,fill)
        fill=m.execute(0x7f,60);p.decide(0,m,60,fill)
        m.execute(0,70);p.decide(0,m,70,0)
        m.execute(0,63)
        self.assertEqual(p.decide(1,m,63,0),0xbf)
        fill=m.execute(0xbf,63)
        self.assertEqual(p.decide(1,m,63,fill),0xbf)
        fill=m.execute(0xbf,63)
        self.assertEqual(p.decide(1,m,63,fill),0)
        for _ in range(32):self.assertEqual(p.decide(1,m,63,0),0)
        self.assertEqual(p.decide(1,m,63,0)>>6,1)

    def test_trend_blocks_buy_but_not_sell(self):
        m=Market(Rules());p=Protection('F')
        for price in range(132,100,-1):p.decide(0,m,price,0)
        self.assertEqual(p.decide(1,m,100,0),0)
        m.execute(0x41,100)
        self.assertEqual(p.decide(-1,m,99,0),0x81)

    def test_exposure_caps_buy_and_corrects_after_price_increase(self):
        m=Market(Rules());p=Protection('E')
        d=p.decide(1,m,100,0)
        self.assertEqual(d,0x40|49)
        m.execute(d,100)
        self.assertLessEqual(m.shares*100,m.equity/2)
        m.execute(0,200)
        d=p.decide(0,m,200,0)
        self.assertEqual(d>>6,2)
        m.execute(d,200)
        self.assertLessEqual(m.shares*200,m.equity/2)

    def test_protected_strategies_are_causal(self):
        prices=[120+(i*17)%31 for i in range(200)]
        for mode in ('P','F','E'):
            _,full=run(prices,'reversion_media',Rules(),policy=Protection(mode))
            _,prefix=run(prices[:100],'reversion_media',Rules(),policy=Protection(mode))
            self.assertEqual(prefix,full[:100])


if __name__=='__main__':unittest.main()
