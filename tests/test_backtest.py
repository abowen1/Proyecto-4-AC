from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from backtest import KINDS, Market, Rules, Strategy, buy_hold_reference, run


class BacktestTests(unittest.TestCase):
    def test_reversion_parameters_against_exact_window(self):
        rng=random.Random(42)
        prices=[rng.randint(1,255) for _ in range(150)]
        for window,band in ((16,2),(32,2),(64,2),(32,1),(32,4)):
            strategy=Strategy('reversion_media',dict(ventana=window,banda=band))
            for i,p in enumerate(prices):
                signal=strategy.observe(p)
                history=prices[max(0,i-window+1):i+1]
                diff=sum(history)-p*window
                expected=0 if len(history)<window else 1 if diff>band*window else -1 if diff<-band*window else 0
                self.assertEqual(signal,expected)
            _,full=run(prices,'reversion_media',Rules(),dict(ventana=window,banda=band))
            _,prefix=run(prices[:90],'reversion_media',Rules(),dict(ventana=window,banda=band))
            self.assertEqual(prefix,full[:90])

    def test_reversion_rejects_invalid_parameters(self):
        for parameters in ({'ventana':0},{'banda':-1},{'ventana':1.5},{'otro':1}):
            with self.assertRaises(ValueError):
                Strategy('reversion_media',parameters)

    def test_delayed_execution_and_last_order_not_executed(self):
        prices = [100] * 8 + [110, 120]
        result, rows = run(prices, 'momentum', Rules())
        self.assertEqual(rows[8]['applied_decision'], 0)
        self.assertEqual(rows[8]['next_decision'], 0x7f)
        self.assertEqual(rows[9]['fill'], 63)
        self.assertEqual(result['shares'], 63)
        self.assertEqual(result['cash'], 2435)
        self.assertEqual(result['equity'], 9995)
        self.assertEqual(result['orders'], 1)

    def test_cash_clipping_no_debt_no_short_and_fees(self):
        m = Market(Rules())
        self.assertEqual(m.execute(0x7f, 255), 39)
        self.assertEqual((m.cash, m.shares, m.orders), (50, 39, 1))
        self.assertEqual(m.execute(0x7f, 255), 0)
        self.assertEqual(m.execute(0xbf, 100), -39)
        self.assertEqual((m.cash, m.shares, m.orders), (3945, 0, 2))
        self.assertEqual(m.execute(0xbf, 100), 0)

    def test_reserved_zero_quantity_and_unaffordable_sale_fee(self):
        m = Market(Rules())
        for d in (0, 63, 0xc0, 0xff, 0x40, 0x80):
            self.assertEqual(m.execute(d, 100), 0)
        self.assertEqual(m.orders, 0)
        m.cash, m.shares = 0, 1
        self.assertEqual(m.execute(0x81, 1), 0)
        self.assertEqual((m.cash,m.shares), (0,1))

    def test_hold_reference_and_mark_to_market_without_final_sale(self):
        result, _ = run([151,100,98], 'mantener', Rules())
        self.assertEqual((result['equity'],result['orders'],result['max_drawdown']), (10000,0,0))
        self.assertEqual(buy_hold_reference([151,98],Rules()),6497)
        m=Market(Rules())
        m.execute(0x41,100)
        m.execute(0,80)
        self.assertEqual((m.equity,m.max_dd),(9975,25))

    def test_every_strategy_is_causal(self):
        prices=[100+(i*17)%31 for i in range(100)]
        for kind in KINDS:
            _, full=run(prices,kind,Rules())
            for length in (8,16,32,47,80):
                _, prefix=run(prices[:length],kind,Rules())
                self.assertEqual(prefix,full[:length],kind)
            self.assertTrue(all(r['cash']>=0 and r['shares']>=0 for r in full))

    def test_incremental_regression_matches_recomputed_window(self):
        rng=random.Random(4)
        prices=[rng.randint(1,255) for _ in range(500)]
        s=Strategy('regresion')
        for i,p in enumerate(prices):
            signal=s.observe(p)
            window=prices[max(0,i-15):i+1]
            self.assertEqual(s.sum_y,sum(window))
            self.assertEqual(s.sum_xy,sum(x*y for x,y in enumerate(window)))
            if len(window)==16:
                n=16; sx=sum(range(n)); sxx=sum(x*x for x in range(n))
                d=n*sxx-sx*sx; a=n*sum(x*y for x,y in enumerate(window))-sx*sum(window)
                diff=sum(window)*d+a*(n*n-sx)-p*n*d
                expected=1 if diff>n*d else -1 if diff<-n*d else 0
                self.assertEqual(signal,expected)


if __name__ == '__main__':
    unittest.main()
