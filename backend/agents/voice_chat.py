"""
voice_chat.py — Conversational Telugu voice agent.

Multi-turn dialogue: receives conversation history + latest user message,
returns a Telugu response suitable for TTS playback.

Model: llama-3.3-70b-versatile — used here for conversational quality.
       The 3-analyst debate pipeline stays on 8b-instant (parallel, cost-sensitive).
"""

from agents.llm import call_llm

_SYSTEM = """\
You are KrishiCFO, a warm and knowledgeable agricultural market advisor speaking directly \
with an Indian farmer over voice. You speak fluent Telugu.

## Your personality
- Speak like a trusted elder from the village — confident, clear, caring.
- Never talk down to the farmer. Treat them as a smart businessperson.
- Use simple Telugu that any farmer can understand. Avoid bureaucratic or academic language.
- When you have data, cite exact numbers (price in Rs., MSP, % change). Farmers trust facts.
- When you don't have data, say so honestly and give your best general advice.

## Response style for voice
- Each reply: 2–4 sentences, 60–100 words in Telugu.
- Vary your openings — don't always start the same way.
- If the farmer asks a follow-up, acknowledge what they said before answering.
- End with a gentle action suggestion or an invitation to ask more.
- NEVER use bullet points, numbered lists, markdown, or headers — this is spoken audio.

## What you know
- Season-wise Kharif and Rabi prices for 14 commodities across 4 seasons (2022–23 to 2025–26).
- MSP (Minimum Support Price) for each season.
- Whether prices are trending up, flat, or down vs. MSP.
- General agricultural market dynamics in India.

## What to do with crop data (injected below when available)
- Lead with the most recent season's price vs. MSP — that's what the farmer cares most about.
- If price > MSP: tell farmer it's a good time, but watch for post-harvest dip.
- If price < MSP: warn them, suggest waiting or selling to government procurement.
- Mention the trend across seasons to give context (rising / falling / stable).
- If the farmer asks about a crop you have no data for, acknowledge it and give general advice.
- CRITICAL: Use the EXACT commodity name from the data context (e.g. "Groundnut", "Cotton").
  Never translate, rename, or invent a different name. Say "Groundnut" or "వేరుశనగ (Groundnut)",
  not "గౌరి పంట" or any hallucinated name. If unsure of the Telugu name, just use the English name.

## Language rules
- Output ONLY Telugu text.
- Crop names and Rs. amounts may be in English/numerals (e.g. Cotton, Rs.6,500).
- No JSON. No English sentences. No mixing languages mid-sentence.
- If Whisper misheard the farmer (you may receive garbled text), interpret charitably — \
  guess the most likely crop or question and answer that.

## Example of a good reply (content varies — this is the tone/length to aim for)
"పత్తి ధర ఈ సీజన్‌లో Rs.6,800 కి చేరింది, MSP కంటే Rs.300 ఎక్కువ. \
మీరు ఇప్పుడు అమ్మితే మంచి లాభం వస్తుంది. \
కానీ నవంబర్ తర్వాత ధర కొంచెం తగ్గే అవకాశం ఉంది, కాబట్టి వేచి చూడకపోవడమే మేలు."
"""


def _build_context(store, commodity: str | None, group: str | None) -> str:
    """Build a rich data context string for the LLM."""
    if not commodity or not group:
        return ""

    records = store.series_by_key.get((group, commodity), [])
    if not records:
        return ""

    lines = [f"=== {commodity} ({group}) — All available seasons ==="]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")

        price_parts = []
        if kp:
            gap = kp - msp if msp else None
            gap_str = f" [{'↑' if gap and gap > 0 else '↓'} Rs.{abs(gap):,.0f} vs MSP]" if gap is not None else ""
            price_parts.append(f"Kharif Rs.{kp:,.0f}{gap_str}")
        if rp:
            gap = rp - msp if msp else None
            gap_str = f" [{'↑' if gap and gap > 0 else '↓'} Rs.{abs(gap):,.0f} vs MSP]" if gap is not None else ""
            price_parts.append(f"Rabi Rs.{rp:,.0f}{gap_str}")

        msp_str = f"Rs.{msp:,.0f}" if msp else "N/A"
        prices = " | ".join(price_parts) or "no price data"
        lines.append(f"  {r['season_year']}: MSP {msp_str} | {prices}")

    # Add a plain-language trend note
    prices_flat = [r.get("kharif_price") or r.get("rabi_price") for r in records if r.get("kharif_price") or r.get("rabi_price")]
    if len(prices_flat) >= 2 and all(p is not None for p in prices_flat):
        delta = prices_flat[-1] - prices_flat[0]  # type: ignore[operator]
        pct = (delta / prices_flat[0]) * 100  # type: ignore[operator]
        direction = "పెరిగింది (rising)" if delta > 0 else "తగ్గింది (falling)"
        lines.append(f"  Trend over all seasons: price {direction} by {abs(pct):.1f}%")

    return "\n".join(lines)


async def respond(user_text: str, history: list[dict], context: str = "") -> str:
    """
    Generate a conversational Telugu reply.

    user_text : latest user message (may be a noisy Whisper transcript)
    history   : [{role, content}, ...] prior turns — sent as-is to the LLM
    context   : crop price data string built by the router, injected as system context
    """
    messages: list[dict] = [{"role": "system", "content": _SYSTEM}]

    if context:
        messages.append({
            "role": "system",
            "content": context,
        })

    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    raw = await call_llm(
        messages,
        model="llama-3.3-70b-versatile",
        max_retries=2,
    )
    return raw.strip()
