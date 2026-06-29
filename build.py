#!/usr/bin/env python3
"""Main build script: fetch → indicators → signals → backtest → render → open."""
import sys
import os
import json
import datetime

sys.path.insert(0, os.path.dirname(__file__))

from lib.fetch import fetch_candles, fetch_quote, fetch_nav, fetch_news, fetch_macro
from lib.indicators import compute_all, aggregate_weekly
from lib.signals import evaluate
from lib.backtest import run_backtest
from lib.render import render_dashboard
from lib.intraday import load as load_intraday, append as append_intraday, save as save_intraday
from lib.commentary import generate as generate_commentary

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "last_good.json")
INTRADAY_PATH = os.path.join(os.path.dirname(__file__), "data", "intraday.json")


def _load_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def build(open_browser=True):
    print("📊 KODEX 인도Nifty50 대시보드 생성 중...")

    # Fetch
    candles = fetch_candles(days=1300)
    if not candles or len(candles) < 30:
        print("⚠️  실시간 데이터 수신 실패 — 캐시 사용")
        fresh = False
        cached = _load_cache()
        if cached:
            candles = cached.get("candles", [])
        if not candles:
            print("❌  데이터 없음. 인터넷 연결을 확인하세요.")
            sys.exit(1)
        quote = cached.get("quote")
        nav = cached.get("nav")
        news = cached.get("news", [])
        macro = cached.get("macro", {})
    else:
        fresh = True
        quote = fetch_quote()
        nav = fetch_nav()
        news = fetch_news()
        macro = fetch_macro()

    print(f"  캔들 {len(candles)}개 수신")

    # Indicators
    indicators = compute_all(candles, quote)
    signal = evaluate(indicators)
    backtest = run_backtest(candles)
    weekly_candles = aggregate_weekly(candles)

    print(f"  시그널: {signal['verdict']} (신뢰도 {signal['confidence']})")
    print(f"  백테스트: {backtest['total_trades']}회 매매, 승률 {backtest['win_rate']}%")

    # 장중 흐름 기록 (신선한 수신일 때만 누적) + 중계 문장
    intraday_state = load_intraday(INTRADAY_PATH)
    if fresh and quote and quote.get("price") is not None:
        intraday_state = append_intraday(intraday_state, quote)
        save_intraday(intraday_state, INTRADAY_PATH)
    commentary = generate_commentary(
        intraday_state.get("points", []), quote, indicators,
        (quote or {}).get("market_status"))

    # Assemble payload
    data = {
        "candles": candles,
        "weekly_candles": weekly_candles,
        "quote": quote,
        "nav": nav,
        "news": news,
        "macro": macro,
        "indicators": indicators,
        "signal": signal,
        "backtest": backtest,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "commentary": commentary,
    }

    # Cache successful fetch
    _save_cache({"candles": candles, "quote": quote, "nav": nav, "news": news, "macro": macro})

    # Render
    render_dashboard(data, OUTPUT_PATH)
    print(f"✅  대시보드 생성 완료: {OUTPUT_PATH}")

    if open_browser:
        import subprocess
        subprocess.Popen(["open", OUTPUT_PATH])
        print("🌐  브라우저에서 열리는 중...")

    return OUTPUT_PATH


if __name__ == "__main__":
    build(open_browser=True)
