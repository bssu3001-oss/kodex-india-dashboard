import unittest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "dashboard.html")


class TestRender(unittest.TestCase):
    def setUp(self):
        from lib.render import render_dashboard
        self.render = render_dashboard

    def test_placeholder_is_replaced(self):
        """After render, __DASHBOARD_DATA__ must not appear in output."""
        data = {"candles": [], "quote": None, "nav": None, "news": [],
                "macro": {}, "indicators": {}, "signal": {}, "backtest": {}, "weekly_candles": []}
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            out_path = f.name
        try:
            self.render(data, out_path)
            with open(out_path) as f:
                content = f.read()
            self.assertNotIn("__DASHBOARD_DATA__", content)
        finally:
            os.unlink(out_path)

    def test_output_contains_valid_json(self):
        """Injected JSON must be parseable."""
        data = {"candles": [{"date":"2026-06-26","open":100,"high":110,"low":90,"close":105,"volume":1000}],
                "quote": None, "nav": None, "news": [], "macro": {},
                "indicators": {}, "signal": {}, "backtest": {}, "weekly_candles": []}
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            out_path = f.name
        try:
            self.render(data, out_path)
            with open(out_path) as f:
                content = f.read()
            # Extract JSON between the script tags
            start = content.find('id="dashboard-data"')
            start = content.find('>', start) + 1
            end = content.find('</script>', start)
            extracted = content[start:end].strip()
            parsed = json.loads(extracted)
            self.assertEqual(parsed["candles"][0]["date"], "2026-06-26")
        finally:
            os.unlink(out_path)

    def test_output_file_is_html(self):
        """Output must start with <!DOCTYPE html> or <html."""
        data = {"candles": [], "quote": None, "nav": None, "news": [],
                "macro": {}, "indicators": {}, "signal": {}, "backtest": {}, "weekly_candles": []}
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            out_path = f.name
        try:
            self.render(data, out_path)
            with open(out_path) as f:
                first_line = f.read(50)
            self.assertTrue(first_line.strip().startswith("<!DOCTYPE") or first_line.strip().startswith("<html"))
        finally:
            os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
