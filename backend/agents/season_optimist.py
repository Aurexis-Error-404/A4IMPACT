import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Season-Optimist analyst for KrishiCFO, an Indian agricultural intelligence system.

Identify positive price signals: seasons where price exceeded MSP, upward trends, \
strong Kharif or Rabi performance.

Respond with ONLY a single JSON object — no text before or after it.

{
  "verdict": "HOLD" | "LEAN_SELL" | "DEFER" | "PROTECT",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentences citing specific seasons and Rs. values>",
  "key_seasons": ["<season_year>", ...]
}

Rules:
- verdict must be exactly one of those four strings
- confidence = strength of your positive signal
- cite actual price numbers from the data
- never fabricate data\
"""


def _prompt(commodity: str, group: str, records: list[dict]) -> str:
    lines = [f"Commodity: {commodity} ({group})", "", "Season data (oldest → latest):"]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")
        parts = []
        if kp:
            parts.append(f"Kharif Rs.{kp:,.2f}")
        if rp:
            parts.append(f"Rabi Rs.{rp:,.2f}")
        price_str = " | ".join(parts) or "No price data"
        lines.append(f"  {r['season_year']}: MSP Rs.{msp:,} | {price_str}")
    lines.append("\nIdentify the strongest positive signals.")
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
    result["agent"] = "optimist"
    return result
