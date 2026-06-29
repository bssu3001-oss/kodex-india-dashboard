"""그날 장중 스냅샷을 data/intraday.json에 누적. 표준 라이브러리만 사용."""
import json
import os
import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "intraday.json")
_KST = datetime.timezone(datetime.timedelta(hours=9))


def _empty():
    return {"date": None, "points": [], "prev_summary": None}


def _kst_dt(quote, now_kst=None):
    """quote.traded_at(이미 +09:00)에서 KST 시각을 얻는다. 없으면 now_kst, 그것도 없으면 현재 UTC→KST."""
    ta = (quote or {}).get("traded_at")
    if ta:
        try:
            return datetime.datetime.fromisoformat(ta).astimezone(_KST)
        except Exception:
            pass
    if now_kst is not None:
        return now_kst
    return datetime.datetime.now(datetime.timezone.utc).astimezone(_KST)


def load(path=DATA_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "points" not in data:
            return _empty()
        data.setdefault("prev_summary", None)
        return data
    except Exception:
        return _empty()


def save(state, path=DATA_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception:
        pass


def append(state, quote, now_kst=None):
    """오늘 스냅샷 추가. 날짜가 바뀌면 새 날로 롤오버(직전 기록을 prev_summary로 이월)."""
    if not isinstance(state, dict) or "points" not in state:
        state = _empty()
    dt = _kst_dt(quote, now_kst)
    today = dt.strftime("%Y-%m-%d")
    t = dt.strftime("%H:%M")
    point = {"t": t, "price": (quote or {}).get("price"),
             "change_pct": (quote or {}).get("change_pct")}

    if state.get("date") != today:
        prev = None
        if state.get("points"):
            prev = {"date": state.get("date"), "points": state.get("points")}
        state = {"date": today, "points": [], "prev_summary": prev}

    pts = state["points"]
    if pts and pts[-1]["t"] == t:
        pts[-1] = point
    else:
        pts.append(point)
    return state
