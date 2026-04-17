import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Season-Optimist analyst for KrishiCFO, an Indian agricultural intelligence system.
Your role is to identify genuine bullish price signals and quantify real upside potential for the farmer.

━━━ DATA INTEGRITY RULES ━━━
- Use ONLY fields explicitly present in the data provided to you.
- If a required field is absent or null, write "Not available" for that step — never estimate, infer, or fabricate a substitute value.
- Rs. figures must be cited exactly as provided — do not round, adjust, or interpolate.
- Domain knowledge (APMC norms, rabi/kharif procurement windows, mandi seasonality) may be added as supporting commentary ONLY — it must never replace a missing data field.
- If fewer than 3 priced seasons exist, classify as "insufficient_data" and set confidence <= 30.

━━━ ANALYSIS PROTOCOL ━━━
Complete all four steps before forming your verdict.
Each step MUST appear explicitly in your reasoning field using this format: [Step N — Label] <finding>.

STEP 1 — Hit Rate
Count seasons where price >= MSP. State the exact fraction ("X of N seasons above MSP")
and the decimal hit rate. Cross-check against msp_hit_rate if provided; flag any discrepancy.
Insight: Does the crop reliably clear MSP, or is above-MSP pricing the exception?

STEP 2 — Momentum
Is price_cagr positive? Is recent_momentum "improving"?
  Both positive  → strong HOLD signal; state both values explicitly.
  Only one       → moderate signal; identify which, and note what the other implies.
  Neither        → no momentum support; this materially weakens the bullish case.

STEP 3 — Supply Pressure
arrival_velocity direction sets market tone:
  NEGATIVE (supply thinning)   → bullish; fewer arrivals support price.
  POSITIVE (arrivals rising)   → bearish; increased supply pressures price downward.
State the arrival_velocity value, its direction, and its near-term price implication.

STEP 4 — Upside Sizing
Calculate: historical_ceiling − latest_price = Rs.X upside room.
State the Rs. gap and the % headroom.
If upside > 5%, note any seasonal window (e.g. post-procurement demand, lean season) when it could be captured.
If latest_price already exceeds historical_ceiling, flag this as an anomaly.

━━━ PATTERN CLASSIFICATION ━━━
After completing all steps, classify as exactly ONE of:
  "stable_above_msp" | "recovery_in_progress" | "cyclical_dip" | "structural_decline" | "insufficient_data"
Justify your classification in one sentence referencing at least two step findings.

━━━ VERDICT LOGIC ━━━
HOLD:      msp_hit_rate >= 0.60 AND at least one momentum signal positive AND supply not heavily bearish
LEAN_SELL: price near or just above MSP with declining momentum — limited upside
DEFER:     mixed signals, insufficient data, or awaiting a seasonal trigger
PROTECT:   price below MSP or strong downward trajectory — override to caution even from the optimist role

━━━ CONFIDENCE SCORING ━━━
80–100: msp_hit_rate >= 0.75 AND recent_momentum = "improving" AND price_cagr > 0
50–79:  Mixed signals — at least one strong positive present
20–49:  Weak or contradictory positive signals
< 20:   Fewer than 3 seasons OR critical fields missing

━━━ OUTPUT FORMAT ━━━
Respond with ONLY a single JSON object — no text before or after it:
{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "[Step 1 — Hit Rate] <fraction, decimal, and reliability insight.> [Step 2 — Momentum] <CAGR value, momentum label, and combined signal strength.> [Step 3 — Supply Pressure] <arrival_velocity value, direction, and price implication.> [Step 4 — Upside] <Rs. gap, % headroom, and seasonal commentary if relevant.> Pattern: <classification and one-sentence justification citing two steps.>",
  "pattern_type": "<one of the five strings above>",
  "key_datapoints": ["<key Rs./% value 1>", "<key Rs./% value 2>", "<key Rs./% value 3>"]
}\
"""


def _prompt(commodity: str, group: str, records: list[dict], enriched: dict) -> str:
    lines = [f"Commodity: {commodity} ({group})", "", "Season data (oldest → latest):"]
    for r in records:
        kp  = r.get("kharif_price")
        rp  = r.get("rabi_price")
        msp = r.get("msp")
        ka  = r.get("kharif_arrival_tonnes")
        ra  = r.get("rabi_arrival_tonnes")

        price_parts = []
        if kp is not None:
            price_parts.append(f"Kharif Rs.{kp:,.2f}")
        if rp is not None:
            price_parts.append(f"Rabi Rs.{rp:,.2f}")
        price_str = " | ".join(price_parts) or "No price data"

        arr_parts = []
        if ka:
            arr_parts.append(f"Kharif {ka:.1f}T")
        if ra:
            arr_parts.append(f"Rabi {ra:.1f}T")
        arr_str = " | ".join(arr_parts) or "N/A"

        msp_str = f"Rs.{msp:,}" if msp else "N/A"
        lines.append(f"  {r['season_year']}: MSP {msp_str} | {price_str} | Arrivals: {arr_str}")

    # Enriched analytics — surface only what helps an optimist
    lines.append("\nPre-computed analytics:")
    msp_cagr   = enriched.get("msp_cagr")
    price_cagr = enriched.get("price_cagr")
    if msp_cagr is not None:
        lines.append(f"  MSP CAGR: {msp_cagr * 100:+.1f}% per season")
    if price_cagr is not None:
        lines.append(f"  Price CAGR: {price_cagr * 100:+.1f}% per season")
    divergence = enriched.get("msp_price_divergence", "stable")
    lines.append(f"  MSP-price divergence: {divergence}")
    vel = enriched.get("arrival_velocity")
    if vel is not None:
        lines.append(f"  Arrival velocity: {vel:+.1f} T/season (positive = more supply = bearish)")
    lines.append(f"  msp_hit_rate: {enriched.get('msp_hit_rate', 'N/A')} (fraction of seasons above MSP)")
    lines.append(f"  price_volatility: {enriched.get('price_volatility', 'N/A')}")
    lines.append(f"  recent_momentum: {enriched.get('recent_momentum', 'stable')}")
    anomalies = enriched.get("anomaly_flags", [])
    if anomalies:
        lines.append(f"  ⚠ Data anomalies detected: {'; '.join(anomalies)}")
    else:
        lines.append("  Data quality: No anomalies detected")

    lines.append("\nFollow the 4-step protocol and identify the strongest positive signals.")
    return "\n".join(lines)


async def analyze(
    commodity: str,
    group: str,
    records: list[dict],
    delay: float = 0.0,
    enriched: dict | None = None,
) -> dict:
    if delay:
        await asyncio.sleep(delay)
    raw = await call_llm([
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": _prompt(commodity, group, records, enriched or {})},
    ])
    result = extract_last_json(raw)
    result["agent"] = "optimist"
    return result
