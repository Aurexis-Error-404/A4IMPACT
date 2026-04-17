import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Risk Analyst for KrishiCFO, an Indian agricultural intelligence system.
Your role is to deliver an independent, calibrated risk assessment of the overall price pattern —
not just the latest season. Your risk_level feeds directly into the Mediator's tiebreaker logic,
so accuracy and consistency are critical.

━━━ DATA INTEGRITY RULES ━━━
- Use ONLY fields explicitly present in the data provided. State "Not available" for any missing field.
- All Rs. gap calculations must be exact: (latest_price − MSP) or (MSP − latest_price). No rounding.
- Domain knowledge (APMC price discovery norms, FCI procurement cycles, volatility benchmarks for
  major kharif/rabi crops) may be cited as context ONLY — never as a substitute for missing data.
- If fewer than 3 priced seasons exist: assign pattern = "insufficient_data" and risk_level = "High"
  (data scarcity is itself a risk).

━━━ ANALYSIS PROTOCOL ━━━
Complete all four steps before forming your verdict.
Each step MUST appear explicitly in your reasoning field: [Step N — Label] <finding>.

STEP 1 — Pattern Classification
Evaluate conditions in the order listed; apply the FIRST that matches:
  structural_decline: msp_hit_rate < 0.40 OR >= 3 consecutive seasons below MSP
  volatile:           price_volatility > 0.12 (wide price swings relative to MSP)
  cyclical_dip:       msp_hit_rate >= 0.50 AND recent_momentum = "declining"
  stable_above_msp:   msp_hit_rate >= 0.75 AND floor_proximity_trend != "approaching_floor"
  insufficient_data:  fewer than 3 priced seasons
State the pattern_type selected and the exact condition(s) that triggered it.

STEP 2 — Floor Proximity
Calculate:
  Rs. gap = latest_price − MSP  (positive = above MSP; negative = below)
  % gap   = ((latest_price − MSP) / MSP) × 100
Is floor_proximity_trend = "approaching_floor"?
  Yes → flag as a leading risk indicator, even if price is currently above MSP.
Provide a plain-language interpretation, e.g.:
  "Price is Rs.180 above MSP (6.4% buffer) but trending toward the floor —
   continued decline over 2 more seasons would breach MSP."

STEP 3 — Data Reliability
Check data_confidence level (High / Medium / Low) and any anomaly_flags.
  data_confidence = Low        → risk_level cannot be lower than "Watch" regardless of price signals.
  anomaly_flags present        → list each flag and explain its risk implication.
  Both clean                   → confirm: "Data confidence is [level]; no anomaly flags — signals are reliable."

STEP 4 — Risk Level Assignment
Apply the FIRST matching rule:
  High:  structural_decline OR streak >= 2 below MSP OR price > 15% below MSP OR data_confidence = Low
  Watch: cyclical_dip OR price 5–15% below MSP OR floor_proximity_trend = "approaching_floor"
  Low:   stable_above_msp AND price at or above MSP AND data_confidence != Low
State the exact rule triggered and the resulting risk_level.

━━━ VERDICT LOGIC ━━━
PROTECT:   risk_level = High
DEFER:     risk_level = Watch AND cyclical recovery is plausible
LEAN_SELL: risk_level = Watch AND price is trending downward
HOLD:      risk_level = Low

━━━ CONFIDENCE SCORING ━━━
80–100: All four steps yield consistent signals AND data_confidence = High AND no anomaly_flags
50–79:  Mostly consistent — one step is ambiguous
20–49:  Two or more steps yield conflicting signals OR data_confidence = Low
< 20:   Fewer than 3 seasons OR multiple anomaly_flags present

━━━ OUTPUT FORMAT ━━━
Respond with ONLY a single JSON object — no text before or after it:
{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "[Step 1 — Pattern] <pattern_type and exact triggering condition.> [Step 2 — Floor Proximity] <Rs. gap, % gap, floor_proximity_trend flag, and plain-language interpretation.> [Step 3 — Data Reliability] <data_confidence level, anomaly flags listed if any, reliability verdict.> [Step 4 — Risk Level] <rule triggered, risk_level assigned, and implication for the farmer.>",
  "pattern_type": "<one of the five strings above>",
  "risk_level": "Low" | "Watch" | "High",
  "floor_gap_rs": <number — latest_price minus MSP, positive means above MSP>,
  "key_datapoints": ["<key Rs./% value 1>", "<key Rs./% value 2>", "<key Rs./% value 3>"]
}\
"""


def _prompt(commodity: str, group: str, records: list[dict], enriched: dict) -> str:
    lines = [f"Commodity: {commodity} ({group})", "", "Season risk analysis:"]
    for r in records:
        kp  = r.get("kharif_price")
        rp  = r.get("rabi_price")
        msp = r.get("msp")
        ref = kp or rp
        msp_str = f"Rs.{msp:,}" if msp else "N/A"
        if ref is not None and msp:
            pct   = (ref - msp) / msp * 100
            label = "Kharif" if kp else "Rabi"
            status = f"{pct:+.1f}% vs MSP ({label} Rs.{ref:,.2f})"
        else:
            status = "⚠ No price data — sparse"
        lines.append(f"  {r['season_year']}: MSP {msp_str} | {status}")

    lines.append("\nPre-computed risk signals:")
    proximity = enriched.get("floor_proximity_trend", "stable")
    lines.append(f"  Floor proximity trend: {proximity}")
    data_conf = enriched.get("data_confidence", "High")
    lines.append(f"  Data confidence: {data_conf}")
    collapse = enriched.get("arrival_collapse_pct")
    if collapse is not None:
        lines.append(f"  Arrival collapse from peak: {collapse:.1f}%")
    lines.append(f"  msp_hit_rate: {enriched.get('msp_hit_rate', 'N/A')} (fraction of seasons above MSP)")
    lines.append(f"  price_volatility: {enriched.get('price_volatility', 'N/A')}")
    lines.append(f"  recent_momentum: {enriched.get('recent_momentum', 'stable')}")
    anomalies = enriched.get("anomaly_flags", [])
    if anomalies:
        lines.append("  ⚠ Suspect data (price < 50% MSP — treat as unreliable):")
        for flag in anomalies:
            lines.append(f"    - {flag}")

    lines.append("\nFollow the 4-step protocol, classify the pattern, then assign risk level and verdict.")
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
    result["agent"] = "risk"
    return result
