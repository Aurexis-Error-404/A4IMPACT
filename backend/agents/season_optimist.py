import asyncio

from agents.llm import call_llm, extract_last_json

_SYSTEM = """\
You are the Season-Optimist analyst for KrishiCFO, an Indian agricultural intelligence system.

Identify positive price signals: seasons where price exceeded MSP, upward trends, \
strong Kharif or Rabi performance, rising arrival volumes.

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
- cite actual price numbers and arrival volumes from the data
- never fabricate data\
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
        lines.append(f"  Arrival velocity: {vel:+.1f} T/season")
    anomalies = enriched.get("anomaly_flags", [])
    if anomalies:
        lines.append(f"  ⚠ Data anomalies detected: {'; '.join(anomalies)}")
    else:
        lines.append("  Data quality: No anomalies detected")

    lines.append("\nIdentify the strongest positive signals.")
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
