from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Mediator for KrishiCFO, an Indian agricultural intelligence system.

You receive verdicts from three analysts and synthesize a final farmer recommendation.

Respond with ONLY a single JSON object — no text before or after it.

CRITICAL — these field values must match EXACTLY (case-sensitive). Any deviation breaks the frontend:

  recommendationLabel: "Hold" | "Lean sell" | "Defer" | "Protect"
  confidenceLabel:     "High confidence" | "Moderate confidence" | "Low confidence"
  riskLevel:           "Low" | "Watch" | "High"

Output format:
{
  "recommendationLabel": "Hold" | "Lean sell" | "Defer" | "Protect",
  "confidenceLabel": "High confidence" | "Moderate confidence" | "Low confidence",
  "riskLevel": "Low" | "Watch" | "High",
  "recommendationRationale": "<2-3 farmer-readable sentences mentioning commodity name and key price facts>",
  "conflict_score": "LOW" | "MEDIUM" | "HIGH"
}

Confidence guidance:
- "High confidence": all 3 agents agree, or 2 agree with confidence ≥ 70
- "Moderate confidence": mixed verdicts or moderate confidence scores
- "Low confidence": agents strongly disagree

conflict_score guidance:
- LOW: agents mostly agree
- MEDIUM: one agent diverges
- HIGH: agents strongly disagree\
"""


def _prompt(
    commodity: str,
    optimist: dict,
    pessimist: dict,
    risk: dict,
    base_insight: dict,
) -> str:
    return "\n".join([
        f"Commodity: {commodity}",
        f"Latest season: {base_insight.get('latestSeason')}",
        f"Price vs MSP: {base_insight.get('latestDeltaLabel')}",
        f"Price trend: {base_insight.get('priceTrend')}",
        "",
        "Agent verdicts:",
        f"  Optimist  — verdict: {optimist.get('verdict')}, confidence: {optimist.get('confidence')}, "
        f"reasoning: {optimist.get('reasoning', 'N/A')}",
        f"  Pessimist — verdict: {pessimist.get('verdict')}, confidence: {pessimist.get('confidence')}, "
        f"reasoning: {pessimist.get('reasoning', 'N/A')}",
        f"  Risk      — verdict: {risk.get('verdict')}, risk_level: {risk.get('risk_level')}, "
        f"confidence: {risk.get('confidence')}, reasoning: {risk.get('reasoning', 'N/A')}",
        "",
        "Synthesize into the final recommendation JSON. Use exact enum strings.",
    ])


async def synthesize(
    commodity: str,
    optimist: dict,
    pessimist: dict,
    risk: dict,
    base_insight: dict,
) -> dict:
    raw = await call_llm(
        [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _prompt(commodity, optimist, pessimist, risk, base_insight)},
        ]
    )
    return extract_last_json(raw)
