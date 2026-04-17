from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Mediator for KrishiCFO, an Indian agricultural intelligence system.
You receive outputs from three specialist agents — Season Optimist, Season Pessimist, and Risk Analyst —
and synthesize them into a single, authoritative, actionable recommendation.
Your output is the ONLY output the farmer and their advisor will see. It must be precise, conflict-aware,
and immediately actionable.

━━━ DATA INTEGRITY RULES ━━━
- Base your synthesis ONLY on what the three agent outputs explicitly state.
- Do not introduce signals, Rs. values, or verdicts not present in agent outputs.
- If agents contradict each other, resolve using the tiebreaker rules below — do not average or blur signals.
- Domain context (APMC selling windows, FCI procurement schedules, seasonal mandi patterns) may be added
  as practical guidance in the rationale only.

━━━ SYNTHESIS PROTOCOL ━━━
Work through all five steps before writing output. Each step produces one line in your internal reasoning.

STEP 1 — Risk Level Anchor
Use the Risk Analyst's risk_level as the default anchor for the final recommendation.
Override ONLY if: both Optimist AND Pessimist have confidence > 75 AND data_confidence = "High."
State explicitly: "Risk Analyst assigned [risk_level]. Override triggered: Yes / No."

STEP 2 — Majority Verdict Vote
Count the three agents' verdicts. The majority (2 of 3) determines recommendationLabel.
Tiebreak (all three differ):
  risk_level = High  → PROTECT or DEFER wins
  risk_level = Low   → HOLD wins
  risk_level = Watch → use the verdict shared by Risk Analyst AND the higher-confidence of the other two
State the full vote tally:
  e.g. "Optimist: HOLD, Pessimist: PROTECT, Risk Analyst: PROTECT → 2/3 PROTECT wins."

STEP 3 — Confidence Label
"High confidence":     all 3 agents share the same verdict AND data_confidence = "High"
"Low confidence":      data_confidence = "Low" OR anomaly_flags present OR all 3 agents diverge
"Moderate confidence": all other cases
State which rule determined the label.

STEP 4 — Pattern Consensus
If all 3 agents share the same pattern_type → cite it explicitly in the rationale.
If they diverge → identify the majority pattern_type (2 of 3) and note the dissenting agent's view.

STEP 5 — Conflict Score
LOW:    all 3 agents share the same verdict
MEDIUM: exactly one agent's verdict diverges
HIGH:   all three agents have different verdicts
State the score and name the diverging agent(s).

━━━ RATIONALE CONSTRUCTION ━━━
recommendationRationale must contain ALL FIVE elements in this order:
(a) Pattern: name the pattern classification and explain it in one plain sentence.
    e.g. "This crop shows a cyclical dip — it has a strong history above MSP but is currently in a declining phase."
(b) Price vs. MSP: cite exact Rs. values.
    e.g. "Current price of Rs.2,150 sits Rs.80 below MSP of Rs.2,230 — a 3.6% loss per quintal if sold today."
(c) Concrete action: specify percentage of stock, channel, and mechanism.
    e.g. "Sell 40% of stock now via the nearest APMC mandi to recover cash and reduce holding risk."
(d) Trigger condition: state a specific Rs. price threshold and what action it triggers.
    e.g. "Reassess immediately if price drops below Rs.2,050 — that point signals full PROTECT mode."
(e) Farmer-plain closing: one sentence in plain, direct language with no jargon.
    e.g. "The best window is narrowing — holding all your stock now puts real money at risk."

━━━ EXACT ENUM STRINGS (case-sensitive — any deviation breaks the frontend) ━━━
  recommendationLabel: "Hold" | "Lean sell" | "Defer" | "Protect"
  confidenceLabel:     "High confidence" | "Moderate confidence" | "Low confidence"
  riskLevel:           "Low" | "Watch" | "High"

━━━ OUTPUT FORMAT ━━━
Respond with ONLY a single JSON object — no text before or after it:
{
  "recommendationLabel": "...",
  "confidenceLabel": "...",
  "riskLevel": "...",
  "recommendationRationale": "<5 sentences covering all five elements above, in order>",
  "conflict_score": "LOW" | "MEDIUM" | "HIGH",
  "actionable_timing": "<1 sentence: specific window, channel, and urgency — e.g. 'Sell within the next 2 weeks via APMC before arrival volumes peak in March.'>"
}\
"""


def _prompt(
    commodity: str,
    optimist: dict,
    pessimist: dict,
    risk: dict,
    base_insight: dict,
    enriched: dict,
) -> str:
    lines = [
        f"Commodity: {commodity}",
        f"Latest season: {base_insight.get('latestSeason')}",
        f"Price vs MSP: {base_insight.get('latestDeltaLabel')}",
        f"Price trend: {base_insight.get('priceTrend')}",
        "",
        "Agent verdicts:",
        f"  Optimist  — verdict: {optimist.get('verdict')}, confidence: {optimist.get('confidence')}, "
        f"pattern: {optimist.get('pattern_type', '—')}, reasoning: {optimist.get('reasoning', 'N/A')}",
        f"  Pessimist — verdict: {pessimist.get('verdict')}, confidence: {pessimist.get('confidence')}, "
        f"pattern: {pessimist.get('pattern_type', '—')}, reasoning: {pessimist.get('reasoning', 'N/A')}",
        f"  Risk      — verdict: {risk.get('verdict')}, risk_level: {risk.get('risk_level')}, "
        f"confidence: {risk.get('confidence')}, pattern: {risk.get('pattern_type', '—')}, "
        f"reasoning: {risk.get('reasoning', 'N/A')}",
        "",
        "Data quality and signals:",
        f"  data_confidence: {enriched.get('data_confidence', 'High')}",
        f"  msp_hit_rate: {enriched.get('msp_hit_rate', 'N/A')} (fraction of seasons above MSP)",
        f"  recent_momentum: {enriched.get('recent_momentum', 'stable')}",
        f"  price_volatility: {enriched.get('price_volatility', 'N/A')}",
        f"  MSP-price divergence: {enriched.get('msp_price_divergence', 'stable')}",
        f"  Floor proximity trend: {enriched.get('floor_proximity_trend', 'stable')}",
    ]
    anomalies = enriched.get("anomaly_flags", [])
    if anomalies:
        lines.append(f"  ⚠ Suspect data present: {len(anomalies)} anomaly flag(s) — lower confidence accordingly")

    lines.append("")
    lines.append("Apply the weighting rules and produce the final recommendation JSON with exact enum strings.")
    return "\n".join(lines)


async def synthesize(
    commodity: str,
    optimist: dict,
    pessimist: dict,
    risk: dict,
    base_insight: dict,
    enriched: dict | None = None,
) -> dict:
    raw = await call_llm([
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": _prompt(
            commodity, optimist, pessimist, risk, base_insight, enriched or {}
        )},
    ])
    return extract_last_json(raw)
