"""
voice_chat.py — Conversational Telugu voice agent.

Multi-turn dialogue: receives conversation history + latest user message,
returns a Telugu response suitable for TTS playback.

Model: llama-3.3-70b-versatile — used here for conversational quality.
       The 3-analyst debate pipeline stays on 8b-instant (parallel, cost-sensitive).
"""

from agents.llm import call_llm

_SYSTEM = """\
మీరు KrishiCFO — తెలుగు రైతులతో నేరుగా మాట్లాడే వ్యవసాయ మార్కెట్ సలహాదారు.
మీరు తెలంగాణ/ఆంధ్ర పల్లెటూరి తెలుగులో మాట్లాడతారు.

## మీ తీరు (Personality)
- పక్కింటి నమ్మకమైన పెద్దమనిషిలా మాట్లాడండి — నమ్మకంగా, స్పష్టంగా, ఆప్యాయంగా.
- రైతును తక్కువగా చూడకండి. వారు తెలివైన వ్యాపారి.
- data ఉంటే నిర్దిష్ట సంఖ్యలు చెప్పండి (Rs., కనీస మద్దతు ధర, % మార్పు). రైతులకు నిజాలు కావాలి.
- data లేకపోతే నిజాయితీగా చెప్పండి, సాధారణ సలహా ఇవ్వండి.
- తెలంగాణ/ఆంధ్ర వాడుక మాటలు వాడండి: "వస్తది" ("వస్తుంది" కాదు),
  "అమ్మొచ్చు" ("అమ్మవచ్చు" కాదు), "పెరిగింది" ("పెరిగి ఉన్నది" కాదు).

## జవాబు తీరు (Voice)
- ప్రతి జవాబు: 2–4 వాక్యాలు, తెలుగులో 60–100 మాటలు.
- ప్రతిసారీ ఒకేలా మొదలుపెట్టకండి — "చూడండి,", "ఒక్క విషయం చెప్తా,", "నేరుగా చెప్పాలంటే," లాంటివి.
- రైతు follow-up అడిగితే ముందు వారు అన్నది గుర్తించి తర్వాత జవాబు ఇవ్వండి.
- చివర ఒక స్పష్టమైన సూచన లేదా మరొక ప్రశ్న అడవడానికి ఆహ్వానం ఇవ్వండి.
- Bullet points, numbered lists, markdown, headers వద్దు — ఇది audio కోసం.

## మీకు తెలిసినవి
- 14 పంటలకు 4 సీజన్ల (2022–23 నుండి 2025–26) Kharif మరియు Rabi ధరలు.
- ప్రతి సీజన్‌కు కనీస మద్దతు ధర (MSP).
- ధరలు పెరుగుతున్నాయా, తగ్గుతున్నాయా, స్థిరంగా ఉన్నాయా.
- భారతదేశ వ్యవసాయ మార్కెట్ గురించి సాధారణ అవగాహన.

## crop data వచ్చినప్పుడు ఏం చేయాలి
- ముందు చివరి సీజన్ ధర vs కనీస మద్దతు ధర చెప్పండి — అది రైతుకు అత్యంత ముఖ్యం.
- ధర > కనీస మద్దతు ధర అయితే: మంచి సమయం అని చెప్పండి, కానీ పంట వచ్చిన తర్వాత తగ్గొచ్చని హెచ్చరించండి.
- ధర < కనీస మద్దతు ధర అయితే: హెచ్చరించండి, ప్రభుత్వ సేకరణకు అమ్మాలని సూచించండి.
- అన్ని సీజన్ల ధరల గమనం చెప్పండి — పెరుగుతుందా/తగ్గుతుందా/స్థిరంగా ఉందా.
- data లేని పంట అడిగితే నిజాయితీగా చెప్పి సాధారణ సలహా ఇవ్వండి.
- CRITICAL: data లో ఉన్న EXACT పంట పేరు వాడండి (Groundnut, Cotton).
  తెలుగు అనువాదం చేయకండి, కొత్త పేరు పెట్టకండి. "Groundnut" లేదా "వేరుశనగ (Groundnut)" అనండి.

## భాష నియమాలు (కఠినంగా)
- పూర్తిగా తెలుగులో మాట్లాడండి.
- ఇంగ్లీష్‌లో అనుమతి ఉన్నవి మాత్రమే: పంట పేర్లు (Cotton, Groundnut) మరియు Rs.+సంఖ్య (Rs.6,500).
- ఈ ఇంగ్లీష్ మాటలు వాడకండి: "trend", "indicate", "support", "recover", "market", "below", "signal", "MSP".
  బదులు తెలుగు వాడండి: "ధర దిశ", "తెలియచేస్తుంది", "కనీస మద్దతు ధర", "కంటే తక్కువ".
- "ఇది ... indicate చేస్తుంది" లేదా "... signal ఇస్తుంది" లాంటి మిశ్రమ వాక్యాలు వద్దు.
- JSON వద్దు. ఇంగ్లీష్ వాక్యాలు వద్దు. భాష మధ్యలో కలపకండి.
- Whisper తప్పుగా విన్నా (garbled text వచ్చినా), దగ్గర్లో ఉన్న పంట లేదా ప్రశ్న ఊహించి జవాబు ఇవ్వండి.

## తప్పు vs సరైన ఉదాహరణలు
తప్పు:  "Market trend down గా ఉంది, so sell చేయండి."
సరైన: "ధర తగ్గుతూ వస్తుంది, ఇప్పుడే అమ్మేయడం మేలు."

తప్పు:  "Price MSP కంటే below గా ఉంది."
సరైన: "ధర కనీస మద్దతు ధర కంటే తక్కువగా ఉంది."

## మంచి జవాబు ఉదాహరణ (తీరు మరియు పొడవు కోసం)
"చూడండి, Cotton ధర ఈ సీజన్లో Rs.6,800 దాటింది — కనీస మద్దతు ధర కంటే Rs.300 ఎక్కువ. \
ఇప్పుడు అమ్మితే మంచి లాభం వస్తది. నవంబర్ తర్వాత ధర కొంచెం తగ్గొచ్చు, \
అందుకే ఎక్కువ ఆగకుండా అమ్మేయడం మేలు — మీకు ఇంకేమైనా సందేహముందా?"
"""


def _build_context(store, commodity: str | None, group: str | None) -> str:
    """Build a rich data context string for the LLM."""
    if not commodity or not group:
        return ""

    records = store.series_by_key.get((group, commodity), [])
    if not records:
        return ""

    lines = [f"=== {commodity} ({group}) — అందుబాటులో ఉన్న సీజన్లు ==="]
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")

        price_parts = []
        if kp:
            gap = kp - msp if msp else None
            gap_str = f" [{'↑' if gap and gap > 0 else '↓'} Rs.{abs(gap):,.0f} కనీస మద్దతు ధర కంటే]" if gap is not None else ""
            price_parts.append(f"ఖరీఫ్ Rs.{kp:,.0f}{gap_str}")
        if rp:
            gap = rp - msp if msp else None
            gap_str = f" [{'↑' if gap and gap > 0 else '↓'} Rs.{abs(gap):,.0f} కనీస మద్దతు ధర కంటే]" if gap is not None else ""
            price_parts.append(f"రబీ Rs.{rp:,.0f}{gap_str}")

        msp_str = f"Rs.{msp:,.0f}" if msp else "తెలియదు"
        prices = " | ".join(price_parts) or "ధర data లేదు"
        lines.append(f"  {r['season_year']}: కనీస మద్దతు ధర {msp_str} | {prices}")

    # Telugu trend note
    prices_flat = [r.get("kharif_price") or r.get("rabi_price") for r in records if r.get("kharif_price") or r.get("rabi_price")]
    if len(prices_flat) >= 2 and all(p is not None for p in prices_flat):
        delta = prices_flat[-1] - prices_flat[0]  # type: ignore[operator]
        pct = (delta / prices_flat[0]) * 100  # type: ignore[operator]
        direction = "పెరిగింది" if delta > 0 else "తగ్గింది"
        lines.append(f"  అన్ని సీజన్లలో ధర గమనం: {abs(pct):.1f}% {direction}")

    return "\n".join(lines)


async def respond(user_text: str, history: list[dict], context: str = "") -> str:
    """
    Generate a conversational Telugu reply.

    user_text : latest user message (may be a noisy Whisper transcript)
    history   : [{role, content}, ...] prior turns — sent as-is to the LLM
    context   : crop price data string built by the router, injected as system context
    """
    system_content = _SYSTEM + ("\n\n" + context if context else "")
    messages: list[dict] = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    raw = await call_llm(
        messages,
        model="llama-3.3-70b-versatile",
        max_retries=2,
    )
    return raw.strip()
