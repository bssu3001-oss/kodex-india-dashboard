from lib.indicators import compute_all
from lib.signals import evaluate


def run_backtest(candles, stop_loss_pct=7.0, take_profit_pct=10.0, warmup=30):
    """
    Walk-forward backtest. No lookahead: signal at day i uses candles[:i+1],
    entry at day i+1 open.
    """
    trades = []
    in_trade = False
    entry_price = entry_date = None

    for i in range(warmup, len(candles) - 1):
        if not in_trade:
            sub = candles[: i + 1]
            try:
                ind = compute_all(sub)
                sig = evaluate(ind)
            except Exception:
                continue
            if sig["verdict"] == "매수 검토":
                entry_price = candles[i + 1]["open"]
                entry_date = candles[i + 1]["date"]
                in_trade = True
        else:
            c = candles[i]
            stop = entry_price * (1 - stop_loss_pct / 100)
            target = entry_price * (1 + take_profit_pct / 100)
            exit_price = exit_date = exit_reason = None
            if c["low"] <= stop:
                exit_price = stop
                exit_reason = "손절"
            elif c["high"] >= target:
                exit_price = target
                exit_reason = "익절"
            if exit_price:
                ret = (exit_price - entry_price) / entry_price * 100
                exit_date = c["date"]
                trades.append({
                    "entry_date": entry_date, "exit_date": exit_date,
                    "entry": entry_price, "exit": exit_price,
                    "return_pct": round(ret, 2), "reason": exit_reason,
                })
                in_trade = False

    if not trades:
        return {"total_trades": 0, "win_rate": 0, "avg_return_pct": 0, "mdd_pct": 0, "trades": []}

    wins = sum(1 for t in trades if t["return_pct"] > 0)
    avg_ret = sum(t["return_pct"] for t in trades) / len(trades)

    # MDD on equity curve (cumulative product)
    equity = 1.0
    peak = 1.0
    mdd = 0.0
    for t in trades:
        equity *= (1 + t["return_pct"] / 100)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > mdd:
            mdd = dd

    return {
        "total_trades": len(trades),
        "win_rate": round(wins / len(trades) * 100, 1),
        "avg_return_pct": round(avg_ret, 2),
        "mdd_pct": round(mdd, 2),
        "trades": trades[-20:],  # last 20 for display
    }
