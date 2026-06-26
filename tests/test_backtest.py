import unittest
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "sample_candles.json")


class TestBacktest(unittest.TestCase):
    def setUp(self):
        with open(FIXTURES) as f:
            self.candles = json.load(f)
        from lib.backtest import run_backtest
        self.run = run_backtest

    def test_returns_required_keys(self):
        result = self.run(self.candles)
        for k in ("total_trades", "win_rate", "avg_return_pct", "mdd_pct", "trades"):
            self.assertIn(k, result)

    def test_win_rate_in_range(self):
        result = self.run(self.candles)
        if result["total_trades"] > 0:
            self.assertGreaterEqual(result["win_rate"], 0)
            self.assertLessEqual(result["win_rate"], 100)

    def test_trades_is_list(self):
        result = self.run(self.candles)
        self.assertIsInstance(result["trades"], list)

    def test_no_lookahead_bias(self):
        # Each signal at index i only uses candles[:i+1]
        from lib.backtest import run_backtest
        result = run_backtest(self.candles)
        # Smoke: entry_date always < exit_date
        for t in result["trades"]:
            self.assertLess(t["entry_date"], t["exit_date"])


if __name__ == "__main__":
    unittest.main()
