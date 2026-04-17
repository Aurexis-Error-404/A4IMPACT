import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Risk Analyst for KrishiCFO, an Indian agricultural intelligence system.

Assess risk based on:
1. Proximity of latest price to MSP (floor proximity risk)
2. Consistency of seasonal data — sparse coverage = higher risk
3. Whether price has been below MSP for multiple seasons in a row

Respond with ONLY a single JSON object — no text before or after it.

{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentences citing specific risk factors>",
  "key_seasons": ["<season_year>", ...],
  "risk_level": "Low" | "Watch" | "High"
}

Rules:
- verdict must be exactly one of: HOLD, LEAN_SELL, DEFER, PROTECT
- risk_level must be exactly: Low | Watch | High  (capital first letter only)
  - High: price > 15% below MSP OR sparse/missing price data
  - Watch: price 5-15% below MSP
  - Low: price at or above MSP
- never fabricate data\
"""


def _prompt(commodity: str, group: str, records: list[dict]) -> str:
    lines = [f"Commodity: {commodity} ({group})", "", "Season risk analysis:"]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")
        ref = kp or rp
        if ref and msp:
            pct = (ref - msp) / msp * 100
            label = "Kharif" if kp else "Rabi"
            status = f"{pct:+.1f}% vs MSP ({label} Rs.{ref:,.2f})"
        else:
            status = "⚠ No price data — sparse"
        lines.append(f"  {r['season_year']}: MSP Rs.{msp:,} | {status}")
    lines.append("\nAssign a risk level and verdict.")
    return "\n".join(lines)


async def analyze(
    commodity: str,
    group: str,
    records: list[dict],
    delay: float = 0.0,
) -> dict:
    if delay:
        await asyncio.sleep(delay)
    raw = await call_llm(
        [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": _prompt(commodity, group, records)}]
    )
    result = extract_last_json(raw)
    result["agent"] = "risk"
    return result
