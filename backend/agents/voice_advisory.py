"""
voice_advisory.py — Single-call advisory for the voice pipeline.

Unlike the full debate pipeline (3 agents + mediator), this uses ONE Llama 8B
call to produce a 2–3 sentence Telugu advisory quickly (<1.5s target).

The output is a short, farmer-readable sentence — NOT JSON.
"""

from agents.llm import call_llm

_SYSTEM = """\
You are KrishiCFO, a Telugu-language commodity intelligence advisor for Indian farmers.
You receive structured season-wise price data for one commodity and must produce
a 2–3 sentence advisory IN TELUGU for the farmer.

Rules:
- Write ONLY Telugu text. No English words except commodity names and Rs. amounts.
- Be direct and actionable: tell the farmer what to do (hold, sell, wait).
- Reference at least one specific data point (MSP, current price, or seasonal trend).
- Keep it under 60 words in Telugu. Farmers listen to this via audio — be conversational.
- Do NOT output JSON. Do NOT output English sentences. Only Telugu prose.

Example output style (content may vary):
"పత్తి ధర ప్రస్తుతం MSP కంటే ఎక్కువగా ఉంది. ఈ సీజన్‌లో అమ్మకం సరైన నిర్ణయం.
రెండు వారాలు ఆగితే ధర ఇంకా పెరిగే అవకాశం ఉంది."
"""


def _build_prompt(commodity: str, group: str, records: list[dict]) -> str:
    lines = [
        f"Commodity: {commodity} ({group})",
        "",
        "Season-wise data (oldest → latest):",
    ]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")

        price_parts = []
        if kp is not None:
            price_parts.append(f"Kharif Rs.{kp:,.2f}")
        if rp is not None:
            price_parts.append(f"Rabi Rs.{rp:,.2f}")
        price_str = " | ".join(price_parts) or "No price data"
        msp_str = f"Rs.{msp:,}" if msp else "N/A"
        lines.append(f"  {r['season_year']}: MSP {msp_str} | {price_str}")

    lines.append("")
    lines.append(
        "Give a short Telugu advisory (2–3 sentences, under 60 words) telling the farmer "
        "whether to hold, sell, or wait with their produce. Be specific and cite at least "
        "one data point."
    )
    return "\n".join(lines)


async def advise(commodity: str, group: str, records: list[dict]) -> str:
    """Return a short Telugu advisory string for voice TTS."""
    raw = await call_llm(
        [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": _build_prompt(commodity, group, records),
            },
        ],
        model="llama-3.1-8b-instant",
        max_retries=2,
    )
    # Strip any accidental whitespace/newlines from LLM output
    return raw.strip()
