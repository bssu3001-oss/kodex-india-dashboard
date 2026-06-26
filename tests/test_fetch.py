import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib.fetch import _norm_candle, _valid_candle, _num


class TestNormCandle(unittest.TestCase):
    def test_normalizes_date(self):
        raw = {"localDate": "20260626", "closePrice": 13125.0,
               "openPrice": 13275.0, "highPrice": 13305.0,
               "lowPrice": 13110.0, "accumulatedTradingVolume": 246700}
        c = _norm_candle(raw)
        self.assertEqual(c["date"], "2026-06-26")

    def test_normalizes_ohlcv(self):
        raw = {"localDate": "20260626", "closePrice": 13125.0,
               "openPrice": 13275.0, "highPrice": 13305.0,
               "lowPrice": 13110.0, "accumulatedTradingVolume": 246700}
        c = _norm_candle(raw)
        self.assertEqual(c["open"], 13275.0)
        self.assertEqual(c["high"], 13305.0)
        self.assertEqual(c["low"], 13110.0)
        self.assertEqual(c["close"], 13125.0)
        self.assertEqual(c["volume"], 246700)

    def test_valid_candle_true(self):
        raw = {"localDate": "20260626", "closePrice": 13125.0,
               "openPrice": 13275.0, "highPrice": 13305.0,
               "lowPrice": 13110.0, "accumulatedTradingVolume": 246700}
        self.assertTrue(_valid_candle(raw))

    def test_valid_candle_missing_field(self):
        self.assertFalse(_valid_candle({"localDate": "20260626"}))


class TestNumHelper(unittest.TestCase):
    def test_parses_comma_number(self):
        self.assertEqual(_num("13,125"), 13125.0)

    def test_parses_pct(self):
        self.assertEqual(_num("+1.26%"), 1.26)

    def test_returns_none_on_empty(self):
        self.assertIsNone(_num(None))
        self.assertIsNone(_num(""))

    def test_parses_negative(self):
        self.assertEqual(_num("-1.39%"), -1.39)


if __name__ == "__main__":
    unittest.main()
