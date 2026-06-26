import urllib.request
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
    # basic: price/change/market_status/traded_at
    basic = _get(f"https://m.stock.naver.com/api/stock/{TICKER}/basic")
    # integration: OHLV, 52w hi/lo, return rates
    integration = _get(f"https://m.stock.naver.com/api/stock/{TICKER}/integration")
    if not basic and not integration:
        return None
    info = {}
    if integration:
        info = {item["code"]: item["value"] for item in integration.get("totalInfos", [])}
    src = basic or {}
    return {
        "price": _num(src.get("closePrice")),
        "change": _num(src.get("compareToPreviousClosePrice")),
        "change_pct": _num(src.get("fluctuationsRatio")),
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
        "market_status": src.get("marketStatus"),
        "traded_at": src.get("localTradedAt"),
    }


def fetch_nav():
    # NAV and deviation rate are in etfKeyIndicator of integration endpoint
    raw = _get(f"https://m.stock.naver.com/api/stock/{TICKER}/integration")
    if not raw:
        return None
    etf = raw.get("etfKeyIndicator") or {}
    nav = etf.get("nav")
    if nav is None:
        return None
    sign = etf.get("deviationSign", "+")
    rate = etf.get("deviationRate")
    gap_pct = None
    if rate is not None:
        gap_pct = round(rate if sign == "+" else -rate, 4)
    return {"nav": _num(str(nav)), "gap_pct": gap_pct}


def fetch_news(count=8):
    """인도 증시 관련 뉴스 (구글 뉴스 RSS). 실패 시 네이버 종목뉴스로 fallback."""
    import urllib.parse
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    queries = ["인도 증시", "인도 ETF"]
    seen = set()
    items = []
    for q in queries:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                root = ET.fromstring(resp.read())
        except Exception:
            continue
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub = it.findtext("pubDate") or ""
            if not title or title in seen:
                continue
            # 인도·Nifty 관련만 남기고 잡음 제거
            if "인도" not in title and "니프티" not in title and "nifty" not in title.lower():
                continue
            seen.add(title)
            try:
                dt = parsedate_to_datetime(pub)
                date = dt.astimezone().strftime("%Y-%m-%d %H:%M")
                sort_key = dt.timestamp()
            except Exception:
                date = pub[:16]
                sort_key = 0.0
            items.append({"title": title, "date": date, "url": link, "_k": sort_key})

    items.sort(key=lambda x: x["_k"], reverse=True)
    result = [{"title": i["title"], "date": i["date"], "url": i["url"]} for i in items[:count]]
    if result:
        return result
    return _fetch_news_naver(count)  # 인도 뉴스 못 받으면 기존 방식으로


def _fetch_news_naver(count=8):
    raw = _get(f"https://m.stock.naver.com/api/news/list?code={TICKER}&pageSize={count}")
    if raw and isinstance(raw, list):
        result = []
        for n in raw[:count]:
            oid = n.get("oid", "")
            aid = n.get("aid", "")
            url = f"https://n.news.naver.com/mnews/article/{oid}/{aid}" if oid and aid else ""
            dt_raw = n.get("dt", "")
            date = f"{dt_raw[:4]}-{dt_raw[4:6]}-{dt_raw[6:8]} {dt_raw[8:10]}:{dt_raw[10:12]}" if len(dt_raw) >= 12 else dt_raw
            result.append({"title": n.get("tit", ""), "date": date, "url": url})
        return result
    return []


def _yahoo_price(symbol):
    """Fetch latest price from Yahoo Finance (stdlib only)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    raw = _get(url)
    try:
        return raw["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception:
        return None


def fetch_macro():
    result = {"usd_krw": None, "usd_inr": None, "nifty50": None}
    result["usd_krw"] = _yahoo_price("USDKRW=X")
    result["usd_inr"] = _yahoo_price("USDINR=X")
    result["nifty50"] = _yahoo_price("%5ENSEI")  # ^NSEI URL-encoded
    return result


def _num(s):
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").replace("%", "").replace("+", ""))
    except (ValueError, TypeError):
        return None
