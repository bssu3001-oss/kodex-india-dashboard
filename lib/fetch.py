import urllib.request
import urllib.error
import json
import datetime

TICKER = "453810"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://m.stock.naver.com/",
}
TIMEOUT = 10


def _get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def fetch_candles(days=200):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days + 60)
    url = (
        f"https://api.stock.naver.com/chart/domestic/item/{TICKER}/day"
        f"?startDateTime={start.strftime('%Y%m%d')}&endDateTime={end.strftime('%Y%m%d')}"
    )
    raw = _get(url)
    if not raw:
        return None
    return [_norm_candle(c) for c in raw if _valid_candle(c)]


def _valid_candle(c):
    return all(k in c for k in ("localDate", "closePrice", "openPrice", "highPrice", "lowPrice", "accumulatedTradingVolume"))


def _norm_candle(c):
    raw_date = c["localDate"]  # "20260626"
    date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
    return {
        "date": date,
        "open": float(c["openPrice"]),
        "high": float(c["highPrice"]),
        "low": float(c["lowPrice"]),
        "close": float(c["closePrice"]),
        "volume": int(c["accumulatedTradingVolume"]),
    }


def fetch_quote():
    url = f"https://m.stock.naver.com/api/stock/{TICKER}/integration"
    raw = _get(url)
    if not raw:
        return None
    info = {item["code"]: item["value"] for item in raw.get("totalInfos", [])}
    return {
        "price": _num(raw.get("closePrice")),
        "change": _num(raw.get("compareToPreviousClosePrice")),
        "change_pct": _num(raw.get("fluctuationsRatio")),
        "open": _num(info.get("openPrice")),
        "high": _num(info.get("highPrice")),
        "low": _num(info.get("lowPrice")),
        "volume": _num(info.get("accumulatedTradingVolume")),
        "high_52w": _num(info.get("highPriceOf52Weeks")),
        "low_52w": _num(info.get("lowPriceOf52Weeks")),
        "ret_1m": info.get("oneMonthEarnRate"),
        "ret_3m": info.get("threeMonthEarnRate"),
        "ret_6m": info.get("sixMonthEarnRate"),
        "ret_1y": info.get("oneYearEarnRate"),
        "market_status": raw.get("marketStatus"),
        "traded_at": raw.get("localTradedAt"),
    }


def fetch_nav():
    url = f"https://m.stock.naver.com/api/stock/{TICKER}/basic"
    raw = _get(url)
    if not raw:
        return None
    # NAV/괴리율은 ETF 전용 필드. 필드명이 없으면 None 반환.
    nav = raw.get("nav") or raw.get("navPrice")
    gap = raw.get("navGapRatio") or raw.get("discountPremiumRatio")
    if nav is None:
        return None
    return {"nav": _num(str(nav)), "gap_pct": _num(str(gap)) if gap is not None else None}


def fetch_news(count=8):
    candidates = [
        f"https://m.stock.naver.com/api/news/stock/{TICKER}?pageSize={count}&page=1",
        f"https://m.stock.naver.com/api/stock/{TICKER}/news?pageSize={count}",
    ]
    for url in candidates:
        raw = _get(url)
        if raw and isinstance(raw, list) and len(raw) > 0:
            return [{"title": n.get("title", ""), "date": n.get("wDateTime", n.get("date", "")),
                     "url": n.get("url", n.get("officialUrl", ""))} for n in raw[:count]]
        if raw and isinstance(raw, dict):
            items = raw.get("list") or raw.get("items") or raw.get("newsList") or []
            if items:
                return [{"title": n.get("title", ""), "date": n.get("wDateTime", n.get("date", "")),
                         "url": n.get("url", n.get("officialUrl", ""))} for n in items[:count]]
    return []


def fetch_macro():
    result = {"usd_krw": None, "usd_inr": None, "nifty50": None}
    # USD/KRW
    fx = _get("https://m.stock.naver.com/api/forex/FX_USDKRW")
    if fx:
        result["usd_krw"] = _num(str(fx.get("closePrice") or fx.get("close", "")))
    # USD/INR
    fx2 = _get("https://m.stock.naver.com/api/forex/FX_USDINR")
    if fx2:
        result["usd_inr"] = _num(str(fx2.get("closePrice") or fx2.get("close", "")))
    # 인도 Nifty50 지수 (해외지수 코드)
    idx = _get("https://m.stock.naver.com/api/index/NIFTY/basic")
    if idx:
        result["nifty50"] = _num(str(idx.get("closePrice") or idx.get("close", "")))
    return result


def _num(s):
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").replace("%", "").replace("+", ""))
    except (ValueError, TypeError):
        return None
