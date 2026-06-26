import unittest
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "sample_candles.json")

def load_candles():
    with open(FIXTURES) as f:
        return json.load(f)


class TestSMA(unittest.TestCase):
    def setUp(self):
        from lib.indicators import sma_series
        self.sma_series = sma_series

    def test_sma5_length(self):
        candles = load_candles()
        result = self.sma_series(candles, 5)
        # sma5 starts from index 4, so len = total - 4
        self.assertEqual(len(result), len(candles) - 4)

    def test_sma5_first_value_is_avg_of_first_5(self):
        candles = load_candles()
        result = self.sma_series(candles, 5)
        expected = sum(c["close"] for c in candles[:5]) / 5
        self.assertAlmostEqual(result[0]["value"], expected, places=2)

    def test_sma_with_insufficient_data_returns_empty(self):
        candles = load_candles()[:3]
        result = self.sma_series(candles, 5)
        self.assertEqual(result, [])


class TestRSI(unittest.TestCase):
    def setUp(self):
        from lib.indicators import rsi_current
        self.rsi = rsi_current

    def test_rsi_in_range(self):
        candles = load_candles()
        val = self.rsi(candles)
        self.assertIsNotNone(val)
        self.assertGreaterEqual(val, 0)
        self.assertLessEqual(val, 100)

    def test_rsi_all_up_approaches_100(self):
        candles = [{"close": float(i * 100)} for i in range(1, 20)]
        val = self.rsi(candles)
        self.assertGreater(val, 90)

    def test_rsi_all_down_approaches_0(self):
        candles = [{"close": float(2000 - i * 100)} for i in range(20)]
        val = self.rsi(candles)
        self.assertLess(val, 10)

    def test_rsi_insufficient_data_returns_none(self):
        from lib.indicators import rsi_current
        val = rsi_current([{"close": 100.0}] * 5)
        self.assertIsNone(val)


class TestATR(unittest.TestCase):
    def setUp(self):
        from lib.indicators import atr_current
        self.atr = atr_current

    def test_atr_positive(self):
        candles = load_candles()
        val = self.atr(candles)
        self.assertIsNotNone(val)
        self.assertGreater(val, 0)

    def test_atr_insufficient_returns_none(self):
        from lib.indicators import atr_current
        self.assertIsNone(atr_current(load_candles()[:5]))


class TestAlignment(unittest.TestCase):
    def setUp(self):
        from lib.indicators import moving_alignment
        self.alignment = moving_alignment

    def test_returns_valid_status(self):
        candles = load_candles()
        result = self.alignment(candles)
        self.assertIn(result["status"], ["정배열", "역배열", "혼조"])

    def test_perfect_alignment(self):
        # MA5 > MA20 > MA60 > MA120 guaranteed when price steadily rises
        candles = [{"date": f"2025-01-{i+1:02d}",
                    "open": float(10000 + i*50), "high": float(10100 + i*50),
                    "low": float(9900 + i*50), "close": float(10000 + i*50),
                    "volume": 100000} for i in range(130)]
        result = self.alignment(candles)
        self.assertEqual(result["status"], "정배열")


class TestSupportResistance(unittest.TestCase):
    def setUp(self):
        from lib.indicators import support_resistance
        self.sr = support_resistance

    def test_returns_lists(self):
        candles = load_candles()
        result = self.sr(candles)
        self.assertIn("supports", result)
        self.assertIn("resistances", result)
        self.assertIsInstance(result["supports"], list)
        self.assertIsInstance(result["resistances"], list)

    def test_supports_below_price(self):
        candles = load_candles()
        current = candles[-1]["close"]
        result = self.sr(candles)
        for s in result["supports"]:
            self.assertLessEqual(s, current * 1.02)  # within 2% tolerance

    def test_resistances_above_price(self):
        candles = load_candles()
        current = candles[-1]["close"]
        result = self.sr(candles)
        for r in result["resistances"]:
            self.assertGreaterEqual(r, current * 0.98)

    def test_resistance_strength_fields_present(self):
        candles = load_candles()
        result = self.sr(candles)
        self.assertIn("resistance_meta", result)
        self.assertIn("strongest_resistance", result)
        # meta는 각 저항선마다 하나씩
        self.assertEqual(len(result["resistance_meta"]), len(result["resistances"]))
        for m in result["resistance_meta"]:
            self.assertIn("touches", m)
            self.assertIn("score", m)
            self.assertEqual(m["score"], m["touches"] + m["confluence"] * 3)

    def test_strongest_resistance_is_highest_score(self):
        candles = load_candles()
        result = self.sr(candles)
        if result["resistances"]:
            self.assertIn(result["strongest_resistance"], result["resistances"])
            best = max(result["resistance_meta"], key=lambda m: m["score"])
            self.assertEqual(result["strongest_resistance"], best["level"])
        else:
            self.assertIsNone(result["strongest_resistance"])


class TestWeeklyAgg(unittest.TestCase):
    def test_weekly_candles_fewer_than_daily(self):
        from lib.indicators import aggregate_weekly
        candles = load_candles()
        weekly = aggregate_weekly(candles)
        self.assertLess(len(weekly), len(candles))

    def test_weekly_high_gte_daily_highs(self):
        from lib.indicators import aggregate_weekly
        candles = load_candles()[:10]
        weekly = aggregate_weekly(candles)
        daily_max_high = max(c["high"] for c in candles)
        weekly_max_high = max(w["high"] for w in weekly)
        self.assertEqual(daily_max_high, weekly_max_high)


if __name__ == "__main__":
    unittest.main()
