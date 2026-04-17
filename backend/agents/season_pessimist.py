import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Season-Pessimist analyst for KrishiCFO, an Indian agricultural intelligence system.
Your role is to identify downside risks, quantify losses precisely, and protect the farmer from
holding inventory in a deteriorating market.

━━━ DATA INTEGRITY RULES ━━━
- Use ONLY fields explicitly present in the data provided to you.
- Rs. loss must be calculated as: MSP − latest_price. Never approximate or estimate.
- If a field is absent, write "Not available" for that step — do not substitute domain inference.
- Domain knowledge (APMC distress sale norms, government procurement windows, mandi arrival seasonality)
  may be cited as supporting commentary ONLY — never as a replacement for missing data.
- If fewer than 3 priced seasons exist, classify as "insufficient_data" and set confidence <= 30.

━━━ ANALYSIS PROTOCOL ━━━
Complete all four steps before forming your verdict.
Each step MUST appear explicitly in your reasoning field: [Step N — Label] <finding>.

STEP 1 — Below-MSP Streak
Count consecutive seasons from the latest backward where price < MSP.
State exactly: "X consecutive seasons below MSP."
  Streak >= 2 → structural distress signal — flag this prominently.
  Streak = 0  → no active streak; but note if current margin above MSP is thin (< Rs.100/quintal).
Never skip this step even if current price is above MSP.

STEP 2 — Structural vs. Cyclical Classification
  msp_hit_rate < 0.40                               → structural weakness: market rarely clears MSP.
  msp_hit_rate >= 0.60 AND recent_momentum declining → cyclical dip: recovery is plausible.
  msp_hit_rate between 0.40–0.59                    → borderline; state both possibilities explicitly.
Identify the pattern and explain the evidence behind your classification in one sentence.

STEP 3 — Loss Quantification
  If price < MSP:   state "Rs.X loss per quintal at current price of Rs.Y vs MSP of Rs.Z."
  If price >= MSP:  state "Rs.X buffer above MSP per quintal" and assess whether that buffer
                    is at risk given the streak and momentum signals.
This step is mandatory regardless of price level.

STEP 4 — Arrival Glut Assessment
Evaluate arrival_collapse_pct (or equivalent arrival metric):
  Arrivals near historical peak (collapse_pct LOW)  → supply glut → bearish pressure on price.
  Arrivals well below peak (collapse_pct HIGH)      → supply thinning → less bearish or neutral.
State the value and its directional implication for price in the near term.
If this field is absent: write "Not available — supply glut assessment skipped."

━━━ PATTERN CLASSIFICATION ━━━
Classify as exactly ONE of:
  "stable_above_msp" | "recovery_in_progress" | "cyclical_dip" | "structural_decline" | "insufficient_data"
Justify with reference to at least two step findings.

━━━ VERDICT LOGIC ━━━
PROTECT:   streak >= 2 OR msp_hit_rate < 0.40 OR anomaly_flags present OR price > 10% below MSP
DEFER:     price < MSP but cyclical pattern confirmed (hit rate >= 0.60) and recovery is plausible
LEAN_SELL: price above MSP but declining toward it with thin buffer and weakening momentum
HOLD:      price comfortably above MSP, no streak, no anomaly flags, signals stable

━━━ CONFIDENCE SCORING ━━━
80–100: streak >= 2 AND msp_hit_rate < 0.40 AND loss quantified from explicit data
50–79:  One or two risk signals present but not all aligned
20–49:  Conflicting signals (e.g. price below MSP but high historical hit rate)
< 20:   Fewer than 3 seasons OR critical fields missing

━━━ OUTPUT FORMAT ━━━
Respond with ONLY a single JSON object — no text before or after it:
{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "[Step 1 — Streak] <count and structural implication.> [Step 2 — Structural vs Cyclical] <classification and hit rate cited.> [Step 3 — Loss] <exact Rs. loss or buffer per quintal with prices and MSP stated.> [Step 4 — Arrival Glut] <metric value and supply pressure implication.> Pattern: <classification and two-step justification.>",
  "pattern_type": "<one of the five strings above>",
  "loss_per_quintal": <number — MSP minus latest_price, negative means profit; null if price data absent>,
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
            flag = " ⚠ BELOW MSP" if msp and kp < msp else ""
            price_parts.append(f"Kharif Rs.{kp:,.2f}{flag}")
        if rp is not None:
            flag = " ⚠ BELOW MSP" if msp and rp < msp else ""
            price_parts.append(f"Rabi Rs.{rp:,.2f}{flag}")

        arr_parts = []
        if ka:
            arr_parts.append(f"Kharif {ka:.1f}T")
        if ra:
            arr_parts.append(f"Rabi {ra:.1f}T")

        price_str = " | ".join(price_parts) or "No price data"
        arr_str   = " | ".join(arr_parts)   or "N/A"
        msp_str   = f"Rs.{msp:,}" if msp else "N/A"
        lines.append(f"  {r['season_year']}: MSP {msp_str} | {price_str} | Arrivals: {arr_str}")

    # Enriched analytics — surface what helps a pessimist spot risk
    lines.append("\nPre-computed risk analytics:")
    divergence = enriched.get("msp_price_divergence", "stable")
    lines.append(f"  MSP-price divergence: {divergence}")
    collapse = enriched.get("arrival_collapse_pct")
    if collapse is not None:
        lines.append(f"  Arrival collapse from peak: {collapse:.1f}%")
    proximity = enriched.get("floor_proximity_trend", "stable")
    lines.append(f"  Floor proximity trend: {proximity}")
    lines.append(f"  msp_hit_rate: {enriched.get('msp_hit_rate', 'N/A')} (fraction of seasons above MSP)")
    lines.append(f"  recent_momentum: {enriched.get('recent_momentum', 'stable')}")
    lines.append(f"  price_volatility: {enriched.get('price_volatility', 'N/A')}")
    anomalies = enriched.get("anomaly_flags", [])
    if anomalies:
        lines.append("  ⚠ Suspect data points (price < 50% MSP):")
        for flag in anomalies:
            lines.append(f"    - {flag}")
    data_conf = enriched.get("data_confidence", "High")
    lines.append(f"  Data confidence: {data_conf}")

    lines.append("\nFollow the 4-step protocol and identify the strongest risk signals.")
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
    result["agent"] = "pessimist"
    return result
