import unittest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib import commentary


def pts(*triples):
    return [{"t": t, "price": p, "change_pct": c} for (t, p, c) in triples]


def quote(price, open_, high, low, change_pct, status):
    return {"price": price, "open": open_, "high": high, "low": low,
            "change_pct": change_pct, "market_status": status}


def ind(vol_pct=0):
    return {"volume": {"trend": "감소", "vs_ma20_pct": vol_pct}}


class TestGenerate(unittest.TestCase):
    def test_waiting_when_no_points(self):
        r = commentary.generate([], quote(None, None, None, None, None, "CLOSE"), ind(), "CLOSE")
        self.assertEqual(r["mode"], "waiting")

    def test_live_mode_basic(self):
        p = pts(("09:00", 13165, 0.0), ("10:30", 13290, 0.95), ("14:00", 13230, 0.8))
        r = commentary.generate(p, quote(13230, 13165, 13295, 13165, 0.8, "OPEN"), ind(-30), "OPEN")
        self.assertEqual(r["mode"], "live")
        self.assertIn("13,165", r["body"])      # 출발가
        self.assertIn("13,230", r["body"])       # 현재가
        self.assertIn("강세 우위", r["body"])
        self.assertTrue(len(r["timeline"]) >= 2)

    def test_close_mode_basic(self):
        p = pts(("09:00", 13165, 0.0), ("15:30", 13230, 0.8))
        r = commentary.generate(p, quote(13230, 13165, 13295, 13165, 0.8, "CLOSE"), ind(10), "CLOSE")
        self.assertEqual(r["mode"], "close")
        self.assertIn("마감", r["title"])
        self.assertIn("강세 마감", r["body"])

    def test_live_uses_prev_close_pct_not_open_basis(self):
        # 갭하락: 시가(13180) < 전일종가, 현재가=전일종가 → 전일 대비 0.00%여야 함(헤더와 일치)
        p = pts(("09:00", 13230, 0.0))
        r = commentary.generate(p, quote(13230, 13180, 13235, 13180, 0.0, "OPEN"), ind(0), "OPEN")
        self.assertIn("전일 대비 +0.00%", r["body"])   # 헤더와 동일 기준·자릿수
        self.assertNotIn("시가 대비", r["body"])         # 시가 대비 % 제거됨

    def test_close_pct_two_decimals(self):
        p = pts(("09:00", 13180, -0.38), ("15:30", 13280, 0.38))
        r = commentary.generate(p, quote(13280, 13180, 13280, 13135, 0.38, "CLOSE"), ind(0), "CLOSE")
        self.assertIn("+0.38%", r["body"])  # 헤더와 동일하게 2자리

    def test_timeline_capped_at_6(self):
        p = pts(*[(f"{9+i//4:02d}:{(i%4)*15:02d}", 13000 + i * 5, 0.1 * i) for i in range(24)])
        r = commentary.generate(p, quote(13115, 13000, 13115, 13000, 0.9, "OPEN"), ind(0), "OPEN")
        self.assertLessEqual(len(r["timeline"]), 6)


if __name__ == "__main__":
    unittest.main()
