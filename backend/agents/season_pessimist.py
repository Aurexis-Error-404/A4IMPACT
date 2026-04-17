import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Season-Pessimist analyst for KrishiCFO, an Indian agricultural intelligence system.

Identify risk signals: seasons where price fell below MSP, declining arrival volumes, \
glut patterns, or sustained underperformance.

Respond with ONLY a single JSON object — no text before or after it.

{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentences citing specific seasons and Rs. values>",
  "key_seasons": ["<season_year>", ...]
}

Rules:
- verdict must be exactly one of those four strings
- confidence = strength of your risk signal
- flag seasons where price < MSP explicitly
- never fabricate data\
"""


def _prompt(commodity: str, group: str, records: list[dict]) -> str:
    lines = [f"Commodity: {commodity} ({group})", "", "Season data (oldest → latest):"]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")
        ka = r.get("kharif_arrival_tonnes")
        ra = r.get("rabi_arrival_tonnes")

        price_parts = []
        if kp:
            flag = " ⚠ BELOW MSP" if msp and kp < msp else ""
            price_parts.append(f"Kharif Rs.{kp:,.2f}{flag}")
        if rp:
            flag = " ⚠ BELOW MSP" if msp and rp < msp else ""
            price_parts.append(f"Rabi Rs.{rp:,.2f}{flag}")

        arrival_parts = []
        if ka:
            arrival_parts.append(f"Kharif {ka:.1f}T")
        if ra:
            arrival_parts.append(f"Rabi {ra:.1f}T")

        price_str = " | ".join(price_parts) or "No price data"
        arr_str = " | ".join(arrival_parts) or "N/A"
        lines.append(f"  {r['season_year']}: MSP Rs.{msp:,} | {price_str} | Arrivals: {arr_str}")
    lines.append("\nIdentify the strongest risk signals.")
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
    result["agent"] = "pessimist"
    return result
