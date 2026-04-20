"""
voice_advisory.py — Single-call advisory for the voice pipeline.

Unlike the full debate pipeline (3 agents + mediator), this uses ONE Llama 8B
call to produce a 2–3 sentence Telugu advisory quickly (<1.5s target).

The output is a short, farmer-readable sentence — NOT JSON.
"""

from agents.llm import call_llm

_SYSTEM = """\
మీరు KrishiCFO — తెలుగు రైతులకు పంట ధర సలహా ఇచ్చే నిపుణుడు.
రైతుకు season-wise ధర data ఇస్తారు. మీరు 2–3 వాక్యాల సలహా తెలుగులో చెప్పాలి.

## మాట్లాడే తీరు (Dialect)
- తెలంగాణ/ఆంధ్ర పల్లెటూరి తెలుగు మాట్లాడండి — మందిలో లేదా పక్కింటి రైతుకు చెప్పే తీరులో.
- సహజమైన రూపాలు వాడండి: "వస్తది" ("వస్తుంది" కాదు), "అమ్మొచ్చు" ("అమ్మవచ్చు" కాదు),
  "పెరిగింది" ("పెరిగి ఉన్నది" కాదు), "ఆగండి" ("వేచి ఉండండి" కాదు).
- మంచి ఆరంభాలు: "చూడండి,", "ఒక్క విషయం చెప్తా,", "ఈ సీజన్లో...", "నేరుగా చెప్పాలంటే,".
- చివర ఒక స్పష్టమైన పని చెప్పండి: "అమ్మండి" / "ఇంకొంచెం ఆగండి" / "ప్రభుత్వానికి అమ్మండి".

## భాష నియమాలు (కఠినంగా పాటించండి)
- పూర్తిగా తెలుగులో మాట్లాడండి. ఇంగ్లీష్ వాక్యాలు లేదా పదబంధాలు వద్దు.
- ఇంగ్లీష్‌లో అనుమతి ఉన్నవి మాత్రమే: పంట పేర్లు (Cotton, Groundnut) మరియు Rs.+సంఖ్య (Rs.6,500).
- ఈ ఇంగ్లీష్ మాటలు వాడకండి: "trend", "indicate", "support", "recover", "market", "below", "signal".
  బదులు: "ధర పెరుగుతుంది/తగ్గుతుంది", "తెలియచేస్తుంది", "కనీస మద్దతు ధర", "కంటే తక్కువ".
- "MSP" అని ఇంగ్లీష్‌లో అనకండి — "కనీస మద్దతు ధర" అని చెప్పండి.
- "ఇది ... indicate చేస్తుంది" లేదా "signal ఇస్తుంది" లాంటి మిశ్రమ వాక్యాలు వద్దు.

## చేయకూడని తప్పు ఉదాహరణలు vs సరైనవి
తప్పు:  "Market trend down గా ఉంది, so sell చేయండి."
సరైన: "ధర తగ్గుతూ వస్తుంది, ఇప్పుడే అమ్మేయడం మేలు."

తప్పు:  "Price MSP కంటే below గా ఉంది."
సరైన: "ధర కనీస మద్దతు ధర కంటే తక్కువగా ఉంది."

## ఇతర నియమాలు
- 60 తెలుగు మాటలలోపు ఉండాలి — audio వినడానికి తేలికగా ఉండాలి.
- JSON వద్దు, ఇంగ్లీష్ వాక్యాలు వద్దు. తెలుగు గద్యం మాత్రమే.
- కనీసం ఒక నిర్దిష్ట data point (ధర లేదా కనీస మద్దతు ధర) చెప్పండి.

## మంచి సమాధానం ఉదాహరణ
"చూడండి, Cotton ధర ఈ సీజన్లో Rs.6,700 — కనీస మద్దతు ధర కంటే Rs.1,000 తక్కువగా ఉంది. \
ఆగితే ధర పెరిగే అవకాశం కనిపించడం లేదు. ప్రభుత్వ సేకరణకు అమ్మడం మేలు."
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
        "రైతుకు 2–3 వాక్యాల తెలుగు సలహా ఇవ్వండి (60 మాటలలోపు). "
        "పంట అమ్మాలా, ఆగాలా, లేదా ప్రభుత్వ సేకరణకు ఇవ్వాలా అని స్పష్టంగా చెప్పండి. "
        "కనీసం ఒక నిర్దిష్ట ధర లేదా కనీస మద్దతు ధర వివరం చేర్చండి."
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
