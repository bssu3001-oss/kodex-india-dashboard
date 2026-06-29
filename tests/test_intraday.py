import unittest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib import intraday


def q(price, change_pct, traded_at):
    return {"price": price, "change_pct": change_pct, "traded_at": traded_at}


class TestAppend(unittest.TestCase):
    def empty(self):
        return {"date": None, "points": [], "prev_summary": None}

    def test_first_point_sets_date_and_kst_time(self):
        s = intraday.append(self.empty(), q(13165, 0.0, "2026-06-29T09:00:12+09:00"))
        self.assertEqual(s["date"], "2026-06-29")
        self.assertEqual(s["points"], [{"t": "09:00", "price": 13165, "change_pct": 0.0}])

    def test_second_point_appends(self):
        s = intraday.append(self.empty(), q(13165, 0.0, "2026-06-29T09:00:00+09:00"))
        s = intraday.append(s, q(13290, 0.95, "2026-06-29T10:30:00+09:00"))
        self.assertEqual(len(s["points"]), 2)
        self.assertEqual(s["points"][1]["t"], "10:30")

    def test_same_minute_replaces_last(self):
        s = intraday.append(self.empty(), q(13165, 0.0, "2026-06-29T09:00:00+09:00"))
        s = intraday.append(s, q(13170, 0.1, "2026-06-29T09:00:40+09:00"))
        self.assertEqual(len(s["points"]), 1)
        self.assertEqual(s["points"][0]["price"], 13170)

    def test_new_day_rolls_and_keeps_prev(self):
        s = intraday.append(self.empty(), q(13165, 0.0, "2026-06-29T09:00:00+09:00"))
        s = intraday.append(s, q(13300, 1.0, "2026-06-30T09:00:00+09:00"))
        self.assertEqual(s["date"], "2026-06-30")
        self.assertEqual(len(s["points"]), 1)
        self.assertEqual(s["prev_summary"]["date"], "2026-06-29")

    def test_load_missing_returns_empty(self):
        s = intraday.load("/nonexistent/path/intraday.json")
        self.assertEqual(s["points"], [])


if __name__ == "__main__":
    unittest.main()
