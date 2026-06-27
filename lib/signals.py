def evaluate(ind):
    """
    ind: output of indicators.compute_all()
    Returns: verdict, confidence, reasons, banner, insight, scenario
    """
    alignment = ind["alignment"]["status"]
    rsi = ind.get("rsi") or 50
    vol_trend = ind["volume"]["trend"]
    vol_vs_ma20 = ind["volume"].get("vs_ma20_pct", 0) or 0
    nearest_sup = ind["sr"].get("nearest_support")
    nearest_res = ind["sr"].get("nearest_resistance")
    strongest_sup = ind["sr"].get("strongest_support")
    strongest_res = ind["sr"].get("strongest_resistance")
    current = ind["position"].get("current", 0)
    dist_sup = round((current - strongest_sup) / current * 100, 2) if (strongest_sup and current) else 999
    dist_res = round((nearest_res - current) / current * 100, 2) if (nearest_res and current) else 999
    golden = ind["crosses"].get("golden")
    dead = ind["crosses"].get("dead")
    atr = ind.get("atr") or (current * 0.015)
    from_high = ind["position"].get("from_60d_high_pct", 0)

    score = 0  # positive = bullish, negative = bearish
    reasons = []

    # --- Trend ---
    if alignment == "정배열":
        score += 2
        reasons.append("이동평균 정배열 (상승 추세)")
    elif alignment == "역배열":
        score -= 3
        reasons.append("이동평균 역배열 (하락 추세) — 매수 보류")
    else:
        reasons.append("이동평균 혼조 — 추세 불명확")

    # --- Golden/Dead cross ---
    if golden and not dead:
        score += 1
        reasons.append(f"골든크로스 발생 ({golden}) — 단기 상승 전환 신호")
    elif dead and not golden:
        score -= 1
        reasons.append(f"데드크로스 발생 ({dead}) — 단기 하락 전환 신호")

    # --- RSI ---
    if rsi >= 70:
        score -= 1
        reasons.append(f"RSI {rsi:.0f} — 과열 구간 (단기 조정 가능)")
    elif rsi <= 30:
        score += 1
        reasons.append(f"RSI {rsi:.0f} — 과매도 구간 (단기 반등 가능)")
    else:
        reasons.append(f"RSI {rsi:.0f} — 정상 범위")

    # --- Volume ---
    if vol_trend == "증가" and vol_vs_ma20 > 20:
        score += 1
        reasons.append("거래량 20일 평균 대비 증가 — 추세에 힘 실림")
    elif vol_trend == "감소":
        score -= 0.5
        reasons.append("거래량 감소 — 추세 신뢰도 낮음")

    # --- Support proximity (buying opportunity) ---
    if dist_sup is not None and dist_sup < 3:
        score += 0.5
        reasons.append(f"지지선 근접 ({dist_sup:.1f}% 위) — 분할 매수 후보")

    # --- Resistance proximity (take profit alert) ---
    if dist_res is not None and dist_res < 3:
        score -= 0.5
        reasons.append(f"저항선 근접 ({dist_res:.1f}% 아래) — 익절/관망 구간")

    # --- Verdict ---
    # 역배열 + 데드크로스 + RSI 과열 + 거래량 감소 등 복합 하락 신호 (score <= -5) → 매도 검토
    if score <= -5 and alignment == "역배열":
        verdict = "매도 검토"
        confidence = "높음"
    elif alignment == "역배열":
        verdict = "관망"
        confidence = "높음"
    elif score >= 3:
        verdict = "매수 검토"
        confidence = "높음"
    elif score >= 1.5:
        verdict = "매수 검토"
        confidence = "보통"
    elif score <= -2:
        verdict = "매도 검토"
        confidence = "보통"
    elif score <= -0.5:
        verdict = "관망"
        confidence = "보통"
    else:
        verdict = "관망"
        confidence = "낮음"

    # --- Banner (역배열 takes highest priority) ---
    banner = None
    if alignment == "역배열":
        banner = "⛔ 하락 추세 진행 중 — 신규 매수 보류"
    elif verdict == "매수 검토" and confidence == "높음":
        banner = f"⚡ 매수 시그널: {', '.join(reasons[:2])}"
    elif rsi >= 75:
        banner = f"⚠️ 단기 과열 주의 (RSI {rsi:.0f}) — 신규 매수 자제"

    # --- Scenario: 분할 매수 플랜 ---
    # 검출된 지지선 전체를 분할 진입가로(가장 강한 지지선도 진입 단계에 포함),
    # 균등 매수 가정 평단가 기준으로 손절·목표·손익비 산출
    supports = ind["sr"].get("supports") or []
    if supports:
        entries = supports[:4]  # 가까운 순, 검출된 지지선 전체(최대 4)
    else:
        entries = [round(current * 0.99, 0)]
    avg_entry = round(sum(entries) / len(entries), 0)  # 균등 분할 평단가

    # 추세이탈선(손절): 가장 깊은 진입(=마지막 지지선) 아래. 그마저 깨지면 추세 이탈
    if atr:
        stop_loss = round(min(entries) - atr * 2, 0)
    else:
        stop_loss = round(min(entries) * 0.97, 0)

    target1 = round(nearest_res, 0) if nearest_res and nearest_res > avg_entry else round(avg_entry * 1.10, 0)

    # 2차 목표 = 1차 목표 위 저항선 중 '가장 강한(가장 많이 막힌)' 것. 없으면 None → "저항 없음"
    res_meta = ind["sr"].get("resistance_meta") or []
    above_t1 = [m for m in res_meta if m["level"] > target1]
    target2 = round(max(above_t1, key=lambda m: m["score"])["level"], 0) if above_t1 else None

    risk = avg_entry - stop_loss
    reward = target1 - avg_entry
    rr = round(reward / risk, 2) if risk > 0 else None

    scenario = {
        "entries": entries,
        "avg_entry": avg_entry,
        "entry": avg_entry,  # 하위호환 (리스크 계산기 프리필 등)
        "stop_loss": stop_loss,
        "target": target1,
        "target2": target2,
        "risk_reward": rr,
        "strongest_support": ind["sr"].get("strongest_support"),
        "strongest_resistance": ind["sr"].get("strongest_resistance"),
        "note": "지지선 분할 매수, 저항선 근처 분할 익절" if verdict == "매수 검토" else "추세 확인 후 분할 진입",
    }

    # --- Insight text ---
    trend_word = "상승" if alignment == "정배열" else ("하락" if alignment == "역배열" else "횡보")
    insight_lines = [
        f"현재 KODEX 인도Nifty50은 이동평균 {alignment} 상태로 {trend_word} 추세입니다.",
        f"RSI {rsi:.0f}은(는) {'과열 구간으로 단기 조정에 주의해야 합니다' if rsi >= 70 else ('과매도 구간으로 반등 가능성이 있습니다' if rsi <= 30 else '정상 범위입니다')}.",
        f"거래량은 20일 평균 대비 {vol_vs_ma20:+.0f}%로 {'힘이 실리고 있습니다' if vol_vs_ma20 > 0 else '약해지고 있습니다'}.",
    ]
    if strongest_sup:
        res_str = f", 저항선은 {nearest_res:,.0f}원 (+{dist_res:.1f}%)" if nearest_res else ""
        insight_lines.append(f"핵심 지지선은 {strongest_sup:,.0f}원 (현재가 대비 -{dist_sup:.1f}%){res_str}입니다.")
    if rr and rr > 0:
        insight_lines.append(f"지지선 균등 분할 매수 시 평단 {avg_entry:,.0f}원 기준 예상 손익비는 {rr:.2f}:1입니다. 손절선 {stop_loss:,.0f}원, 1차 목표 {target1:,.0f}원.")
    insight_lines.append("※ 분석 결과이며 투자 권유가 아닙니다. 매매 시 손절선 준수와 분할 진입을 권장합니다.")

    return {
        "verdict": verdict,
        "confidence": confidence,
        "score": round(score, 1),
        "reasons": reasons,
        "banner": banner,
        "insight": " ".join(insight_lines),
        "scenario": scenario,
    }
