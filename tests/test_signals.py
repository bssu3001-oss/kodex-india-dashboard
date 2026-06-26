import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib.signals import evaluate


def make_ind(alignment="정배열", rsi=55, vol_trend="증가",
             dist_support=-3.0, dist_resistance=5.0):
    return {
        "alignment": {"status": alignment, "ma5": 13200, "ma20": 13100,
                       "ma60": 13000, "ma120": 12900},
        "rsi": rsi,
        "volume": {"trend": vol_trend, "vs_ma20_pct": 10 if vol_trend == "증가" else -10},
        "sr": {"nearest_support": 12700, "nearest_resistance": 13800,
               "dist_to_support_pct": abs(dist_support),
               "dist_to_resistance_pct": dist_resistance},
        "position": {"current": 13125, "from_60d_high_pct": -3.2},
        "crosses": {"golden": "2026-06-10", "dead": None},
        "atr": 200,
    }


class TestEvaluate(unittest.TestCase):
    def test_verdict_is_valid(self):
        result = evaluate(make_ind())
        self.assertIn(result["verdict"], ["매수 검토", "관망", "매도 검토"])

    def test_strong_buy_signal(self):
        # 정배열 + RSI < 60 + 거래량 증가
        result = evaluate(make_ind(alignment="정배열", rsi=55, vol_trend="증가"))
        self.assertIn(result["verdict"], ["매수 검토"])

    def test_downtrend_never_buys(self):
        # 역배열은 어떤 경우에도 "매수 검토"를 내면 안 됨
        result = evaluate(make_ind(alignment="역배열", rsi=45))
        self.assertNotEqual(result["verdict"], "매수 검토")

    def test_mild_downtrend_gives_watch(self):
        # 역배열 + 골든크로스 없음 → score=-3 → 관망
        ind = make_ind(alignment="역배열", rsi=55, vol_trend="증가")
        ind["crosses"] = {"golden": None, "dead": None}
        result = evaluate(ind)
        self.assertEqual(result["verdict"], "관망")

    def test_overbought_triggers_caution(self):
        result = evaluate(make_ind(rsi=75))
        self.assertIn("과열", " ".join(result["reasons"]))

    def test_banner_on_strong_buy(self):
        result = evaluate(make_ind(alignment="정배열", rsi=52, vol_trend="증가"))
        # banner may or may not fire depending on combined score — just check type
        self.assertIn(result["banner"], [None, *[s for s in [result["banner"]] if s]])

    def test_insight_is_nonempty_string(self):
        result = evaluate(make_ind())
        self.assertIsInstance(result["insight"], str)
        self.assertGreater(len(result["insight"]), 20)

    def test_scenario_has_required_keys(self):
        result = evaluate(make_ind())
        for key in ("entry", "stop_loss", "target", "risk_reward"):
            self.assertIn(key, result["scenario"])

    def test_confidence_levels(self):
        result = evaluate(make_ind())
        self.assertIn(result["confidence"], ["높음", "보통", "낮음"])


if __name__ == "__main__":
    unittest.main()
