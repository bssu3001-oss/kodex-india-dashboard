import datetime


def sma_series(candles, period):
    closes = [c["close"] for c in candles]
    if len(closes) < period:
        return []
    result = []
    for i in range(period - 1, len(closes)):
        val = sum(closes[i - period + 1 : i + 1]) / period
        result.append({"date": candles[i]["date"], "value": round(val, 2)})
    return result


def sma_current(candles, period):
    series = sma_series(candles, period)
    return series[-1]["value"] if series else None


def rsi_current(candles, period=14):
    closes = [c["close"] for c in candles]
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def atr_current(candles, period=14):
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return round(atr, 1)


def moving_alignment(candles):
    ma5 = sma_current(candles, 5)
    ma20 = sma_current(candles, 20)
    ma60 = sma_current(candles, 60)
    ma120 = sma_current(candles, 120)
    available = {k: v for k, v in {"ma5": ma5, "ma20": ma20, "ma60": ma60, "ma120": ma120}.items() if v is not None}
    vals = [ma5, ma20, ma60, ma120]
    defined = [v for v in vals if v is not None]
    if len(defined) < 2:
        status = "데이터 부족"
    elif all(defined[i] >= defined[i + 1] for i in range(len(defined) - 1)):
        status = "정배열"
    elif all(defined[i] <= defined[i + 1] for i in range(len(defined) - 1)):
        status = "역배열"
    else:
        status = "혼조"
    current = candles[-1]["close"] if candles else None
    return {
        "status": status,
        "ma5": ma5, "ma20": ma20, "ma60": ma60, "ma120": ma120,
        "gap_pct": {
            k: round((current - v) / v * 100, 2) if current and v else None
            for k, v in available.items()
        },
    }


def detect_crosses(candles):
    """Detect the most recent golden/dead cross between MA5 and MA20."""
    if len(candles) < 21:
        return {"golden": None, "dead": None}
    golden = dead = None
    for i in range(20, len(candles)):
        sub = candles[: i + 1]
        prev = candles[: i]
        m5_now = sma_current(sub, 5)
        m20_now = sma_current(sub, 20)
        m5_prev = sma_current(prev, 5)
        m20_prev = sma_current(prev, 20)
        if None in (m5_now, m20_now, m5_prev, m20_prev):
            continue
        if m5_prev < m20_prev and m5_now >= m20_now:
            golden = candles[i]["date"]
        elif m5_prev > m20_prev and m5_now <= m20_now:
            dead = candles[i]["date"]
    return {"golden": golden, "dead": dead}


def support_resistance(candles, lookback=60):
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    current = candles[-1]["close"]

    # Swing highs/lows (window=3)
    swing_highs = []
    swing_lows = []
    for i in range(2, len(recent) - 2):
        h = recent[i]["high"]
        l = recent[i]["low"]
        if h == max(c["high"] for c in recent[i - 2 : i + 3]):
            swing_highs.append(h)
        if l == min(c["low"] for c in recent[i - 2 : i + 3]):
            swing_lows.append(l)

    # Add key MAs as S/R candidates
    for p in (20, 60, 120):
        v = sma_current(candles, p)
        if v:
            if v < current:
                swing_lows.append(v)
            else:
                swing_highs.append(v)

    def cluster(prices, threshold_pct=0.5):
        if not prices:
            return []
        prices = sorted(set(round(p, 0) for p in prices))
        clusters = [[prices[0]]]
        for p in prices[1:]:
            if abs(p - clusters[-1][-1]) / clusters[-1][-1] * 100 < threshold_pct:
                clusters[-1].append(p)
            else:
                clusters.append([p])
        return [round(sum(c) / len(c), 0) for c in clusters]

    supports = sorted([p for p in cluster(swing_lows) if p < current * 1.02], reverse=True)[:4]
    resistances = sorted([p for p in cluster(swing_highs) if p > current * 0.98])[:4]

    nearest_support = supports[0] if supports else None
    nearest_resistance = resistances[0] if resistances else None

    return {
        "supports": supports,
        "resistances": resistances,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "dist_to_support_pct": round((current - nearest_support) / current * 100, 2) if nearest_support else None,
        "dist_to_resistance_pct": round((nearest_resistance - current) / current * 100, 2) if nearest_resistance else None,
    }


def volume_analysis(candles):
    if len(candles) < 20:
        return {"trend": "데이터 부족", "vs_ma5": None, "vs_ma20": None}
    vols = [c["volume"] for c in candles]
    ma5v = sum(vols[-5:]) / 5
    ma20v = sum(vols[-20:]) / 20
    current_vol = vols[-1]
    return {
        "current": current_vol,
        "ma5": round(ma5v),
        "ma20": round(ma20v),
        "vs_ma5_pct": round((current_vol - ma5v) / ma5v * 100, 1),
        "vs_ma20_pct": round((current_vol - ma20v) / ma20v * 100, 1),
        "trend": "증가" if current_vol > ma5v else "감소",
    }


def high_low_position(candles, quote=None):
    """고점/저점 대비 현재가 위치."""
    if not candles:
        return {}
    current = (quote["price"] if quote and quote.get("price") else candles[-1]["close"])
    recent_high = max(c["high"] for c in candles[-60:]) if len(candles) >= 60 else max(c["high"] for c in candles)
    recent_low = min(c["low"] for c in candles[-60:]) if len(candles) >= 60 else min(c["low"] for c in candles)
    high_52w = max(c["high"] for c in candles)
    low_52w = min(c["low"] for c in candles)
    return {
        "current": current,
        "from_60d_high_pct": round((current - recent_high) / recent_high * 100, 2),
        "from_60d_low_pct": round((current - recent_low) / recent_low * 100, 2),
        "from_52w_high_pct": round((current - high_52w) / high_52w * 100, 2),
        "from_52w_low_pct": round((current - low_52w) / low_52w * 100, 2),
        "position_52w_pct": round((current - low_52w) / (high_52w - low_52w) * 100, 1) if high_52w != low_52w else 50.0,
    }


def aggregate_weekly(candles):
    weekly = {}
    for c in candles:
        dt = datetime.date.fromisoformat(c["date"])
        # ISO week Monday
        monday = dt - datetime.timedelta(days=dt.weekday())
        key = monday.isoformat()
        if key not in weekly:
            weekly[key] = {"date": key, "open": c["open"], "high": c["high"],
                           "low": c["low"], "close": c["close"], "volume": c["volume"]}
        else:
            weekly[key]["high"] = max(weekly[key]["high"], c["high"])
            weekly[key]["low"] = min(weekly[key]["low"], c["low"])
            weekly[key]["close"] = c["close"]
            weekly[key]["volume"] += c["volume"]
    return sorted(weekly.values(), key=lambda x: x["date"])


def compute_all(candles, quote=None):
    """One-shot: compute all indicators and return a single dict."""
    alignment = moving_alignment(candles)
    crosses = detect_crosses(candles)
    sr = support_resistance(candles)
    vol = volume_analysis(candles)
    pos = high_low_position(candles, quote)
    rsi = rsi_current(candles)
    atr = atr_current(candles)

    return {
        "alignment": alignment,
        "crosses": crosses,
        "sr": sr,
        "volume": vol,
        "position": pos,
        "rsi": rsi,
        "atr": atr,
        "sma": {
            "5": sma_series(candles, 5),
            "20": sma_series(candles, 20),
            "60": sma_series(candles, 60),
            "120": sma_series(candles, 120),
        },
    }
