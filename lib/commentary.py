"""흐름 기록 + 현재 quote → 규칙 기반 중계 문장(담백한 해설체, 존댓말). 표준 라이브러리만."""


def _fmt(n):
    try:
        return f"{round(n):,}"
    except Exception:
        return "–"


def _signed(n):
    return f"{'+' if n >= 0 else ''}{n:.1f}%"


def _build_timeline(points):
    p = [x for x in points if x.get("price") is not None]
    n = len(p)
    if n == 0:
        return []
    if n <= 6:
        idxs = list(range(n))
    else:
        hi = max(range(n), key=lambda i: p[i]["price"])
        lo = min(range(n), key=lambda i: p[i]["price"])
        idxs = set([0, hi, lo, n - 1])
        i = 0
        while len(idxs) < 6 and i < n:
            idxs.add(i)
            i += max(1, n // 6)
        idxs = sorted(idxs)[:6]
        idxs = sorted(set(idxs))
    return [f"{p[i]['t']} {_fmt(p[i]['price'])}" for i in idxs]


def _vol_phrase(indicators):
    vol = (indicators or {}).get("volume") or {}
    v = vol.get("vs_ma20_pct")
    if v is None:
        return ""
    if v > 20:
        return " 거래량은 평소보다 많습니다."
    if v < -20:
        return " 거래량은 평소보다 다소 적습니다."
    return " 거래량은 평소 수준입니다."


def generate(points, quote, indicators, market_status):
    q = quote or {}
    price = q.get("price")
    open_ = q.get("open")
    change_pct = q.get("change_pct")
    points = points or []

    if not points or price is None:
        return {"mode": "waiting", "title": "오늘의 흐름",
                "body": "장 시작 대기 중입니다.", "timeline": []}

    prices = [p["price"] for p in points if p.get("price") is not None]
    day_high = max(prices) if prices else q.get("high")
    day_low = min(prices) if prices else q.get("low")
    start = points[0].get("price") or open_

    vs_open = round((price - start) / start * 100, 1) if start else None
    strong = (vs_open is not None and vs_open > 0) and (change_pct is not None and change_pct > 0)
    weak = (vs_open is not None and vs_open < 0) and (change_pct is not None and change_pct < 0)
    mood = "강세 우위" if strong else ("약세 우위" if weak else "보합권")
    vol = _vol_phrase(indicators)

    if market_status == "CLOSE":
        if open_ and price and price > open_:
            close_word = "강세 마감"
        elif open_ and price and price < open_:
            close_word = "약세 마감"
        else:
            close_word = "보합 마감"
        span = round((day_high - day_low) / day_low * 100, 1) if (day_high and day_low) else None
        body = f"{_fmt(start)}로 출발, 장중 {_fmt(day_high)}까지 올랐다 {_fmt(price)}으로 마감"
        if change_pct is not None:
            body += f"({_signed(change_pct)})"
        body += f". 시가 대비 {close_word}입니다. 고점 {_fmt(day_high)} / 저점 {_fmt(day_low)}"
        if span is not None:
            body += f", 변동폭 {span:.1f}%"
        body += "." + vol
        return {"mode": "close", "title": "✅ 오늘 마감 요약", "body": body.strip(), "timeline": []}

    # live
    body = f"{_fmt(start)}로 출발해 "
    if day_high and price and day_high > price:
        body += f"장중 {_fmt(day_high)}까지 올랐다가 현재 {_fmt(price)}"
    else:
        body += f"현재 {_fmt(price)}"
    body += f", 시가 대비 {_signed(vs_open)}입니다" if vs_open is not None else "입니다"
    body += f". 오늘 고점 {_fmt(day_high)} / 저점 {_fmt(day_low)}"
    body += f", 전일 대비 {_signed(change_pct)}로 {mood}입니다" if change_pct is not None else f", {mood}입니다"
    body += "." + vol
    return {"mode": "live", "title": "📡 오늘의 흐름", "body": body.strip(),
            "timeline": _build_timeline(points)}
