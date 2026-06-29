import unittest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "sample_candles.json")


def make_quote():
    return {"price": 13125, "change": -185, "change_pct": -1.39, "open": 13275,
            "high": 13305, "low": 13110, "volume": 246700,
            "high_52w": 14782, "low_52w": 12090,
            "ret_1m": "+4.72%", "ret_3m": "+5.30%", "ret_6m": "-7.27%", "ret_1y": "-1.25%",
            "market_status": "CLOSE", "traded_at": "2026-06-26T16:01:19+09:00"}


class TestBuildIntegration(unittest.TestCase):
    def setUp(self):
        with open(FIXTURES) as f:
            self.candles = json.load(f)

    def _patch_and_build(self, out_path):
        """Monkey-patch all fetch functions, point OUTPUT_PATH / INTRADAY_PATH to temp files."""
        import lib.fetch as fetch_mod
        import build as build_mod
        intraday_path = out_path + ".intraday.json"
        orig_intraday = build_mod.INTRADAY_PATH
        # Patch
        build_mod.OUTPUT_PATH = out_path
        build_mod.INTRADAY_PATH = intraday_path
        build_mod.fetch_candles = lambda days=200: self.candles
        build_mod.fetch_quote = lambda: make_quote()
        build_mod.fetch_nav = lambda: {"nav": 13100, "gap_pct": 0.19}
        build_mod.fetch_news = lambda: [{"title": "Test", "date": "2026-06-26", "url": ""}]
        build_mod.fetch_macro = lambda: {"usd_krw": 1380.0, "usd_inr": 83.5, "nifty50": 24500.0}
        result = build_mod.build(open_browser=False)
        # Restore
        build_mod.OUTPUT_PATH = os.path.join(os.path.dirname(build_mod.__file__), "dashboard.html")
        build_mod.INTRADAY_PATH = orig_intraday
        build_mod.fetch_candles = fetch_mod.fetch_candles
        build_mod.fetch_quote = fetch_mod.fetch_quote
        build_mod.fetch_nav = fetch_mod.fetch_nav
        build_mod.fetch_news = fetch_mod.fetch_news
        build_mod.fetch_macro = fetch_mod.fetch_macro
        if os.path.exists(intraday_path):
            os.unlink(intraday_path)
        return result

    def test_build_produces_html(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            out_path = f.name
        try:
            self._patch_and_build(out_path)
            with open(out_path) as f:
                content = f.read()
            self.assertIn("KODEX", content)
            self.assertNotIn("__DASHBOARD_DATA__", content)
        finally:
            os.unlink(out_path)

    def test_build_injects_candles(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            out_path = f.name
        try:
            self._patch_and_build(out_path)
            with open(out_path) as f:
                content = f.read()
            # JSON should contain candle dates
            self.assertIn("2026-04-29", content)  # last date in fixture
        finally:
            os.unlink(out_path)

    def test_build_returns_output_path(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            out_path = f.name
        try:
            result = self._patch_and_build(out_path)
            self.assertEqual(result, out_path)
        finally:
            os.unlink(out_path)

    def test_commentary_present_in_output(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            out_path = f.name
        try:
            self._patch_and_build(out_path)
            with open(out_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn('"commentary"', content)
            self.assertIn("오늘 마감 요약", content)  # make_quote는 CLOSE 상태
        finally:
            os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
