import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestSmoke(unittest.TestCase):
    def test_import_fetch(self):
        import lib.fetch
        self.assertTrue(hasattr(lib.fetch, "fetch_candles"))
        self.assertTrue(hasattr(lib.fetch, "fetch_quote"))
        self.assertTrue(hasattr(lib.fetch, "fetch_nav"))
        self.assertTrue(hasattr(lib.fetch, "fetch_news"))
        self.assertTrue(hasattr(lib.fetch, "fetch_macro"))

    def test_import_indicators(self):
        import lib.indicators
        self.assertTrue(hasattr(lib.indicators, "compute_all"))
        self.assertTrue(hasattr(lib.indicators, "aggregate_weekly"))

    def test_import_signals(self):
        import lib.signals
        self.assertTrue(hasattr(lib.signals, "evaluate"))

    def test_import_backtest(self):
        import lib.backtest
        self.assertTrue(hasattr(lib.backtest, "run_backtest"))

    def test_import_render(self):
        import lib.render
        self.assertTrue(hasattr(lib.render, "render_dashboard"))

    def test_import_build(self):
        import build
        self.assertTrue(hasattr(build, "build"))

    def test_template_exists(self):
        template = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "dashboard.html")
        self.assertTrue(os.path.exists(template), f"Template missing: {template}")

    def test_vendor_exists(self):
        vendor = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor", "lightweight-charts.standalone.production.js")
        self.assertTrue(os.path.exists(vendor), f"Vendor JS missing: {vendor}")


if __name__ == "__main__":
    unittest.main()
