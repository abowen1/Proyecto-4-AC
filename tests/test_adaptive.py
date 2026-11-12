from decimal import Decimal, localcontext
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare_adaptive import AdaptiveReversion, simulate


class AdaptiveTests(unittest.TestCase):
    def test_signal_matches_independent_decimal_standard_deviation(self):
        rng = random.Random(42)
        prices = [rng.randint(1, 255) for _ in range(1500)]
        for denominator in (1, 2):
            model = AdaptiveReversion(1, denominator)
            for i, p in enumerate(prices):
                actual = model.observe(p)
                if i < 31:
                    self.assertEqual(actual, 0)
                    continue
                with localcontext() as ctx:
                    ctx.prec = 60
                    window = list(map(Decimal, prices[i-31:i+1]))
                    mean = sum(window) / 32
                    sigma = (sum((x-mean)**2 for x in window) / 32).sqrt()
                    delta, threshold = mean - p, sigma / denominator
                    expected = 1 if delta > threshold else -1 if delta < -threshold else 0
                self.assertEqual(actual, expected)

    def test_equality_flat_window_and_scaling(self):
        a, d = AdaptiveReversion(window=4), AdaptiveReversion(1,2,4)
        for p in (100,100,104):
            self.assertEqual(a.observe(p), 0)
            self.assertEqual(d.observe(p), 0)
        self.assertEqual(a.observe(104), 0)  # exactly one sigma, strict threshold
        self.assertEqual(d.observe(104), -1)
        flat = AdaptiveReversion()
        self.assertEqual([flat.observe(100) for _ in range(100)], [0]*100)
        original, transformed = AdaptiveReversion(), AdaptiveReversion()
        for p in [10 + (i*17)%31 for i in range(200)]:
            self.assertEqual(original.observe(p), transformed.observe(p*3+7))

    def test_run_is_causal_and_executes_next_tick(self):
        prices = [100]*31 + [50,60,130] + [100]*70
        for name in ('Ad', 'Dd'):
            _, full = simulate(prices, name)
            _, prefix = simulate(prices[:50], name)
            self.assertEqual(prefix, full[:50])
            self.assertEqual(full[31]['fill'], 0)
            self.assertGreater(full[31]['next_decision'] & 63, 0)
            self.assertGreater(full[32]['fill'], 0)
            self.assertEqual(full[32]['applied_decision'], full[31]['next_decision'])


if __name__ == '__main__':
    unittest.main()
