"""
voice.py — Voice pipeline router.

POST /voice/transcribe  → STT only (audio → text)
POST /voice/query       → full voice pipeline: STT → entity extract → advisory → TTS

STT:  Groq Whisper Large v3 (same API key, language="te" for Telugu)
TTS:  ElevenLabs Multilingual v2 (5s timeout, falls back to text-only if it fails)

Response shape (both endpoints share the text fields; /query adds audio if TTS succeeds):
{
  "transcript_te":       str,             # Raw Telugu transcript from Whisper
  "transcript_en":       str,             # English translation (used for entity extraction)
  "commodity_detected":  str | null,      # Matched commodity name from dataset
  "text_response_te":    str,             # Telugu advisory text
  "audio_base64":        str | null,      # base64 MP3 from ElevenLabs, or null
}
"""

import asyncio
import base64
import io
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from groq import AsyncGroq

import json

from agents.voice_advisory import advise
from agents.voice_chat import respond as chat_respond
from config import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])
settings = Settings()

# ---------------------------------------------------------------------------
# Commodity name list — used for fuzzy entity extraction
# ---------------------------------------------------------------------------
# Actual commodity names from the store (verified):
# Cereals: Jowar(Sorghum), Maize, Paddy(Common)
# Fibre Crops: Cotton
# Oil Seeds: Groundnut, Mustard, Safflower, Sesamum(Sesame,Gingelly,Til), Soyabean, Sunflower/Sunflower Seed
# Pulses: Arhar(Tur/Red Gram)(Whole), Bengal Gram(Gram)(Whole), Black Gram(Urd Beans)(Whole), Green Gram(Moong)(Whole)

_COMMODITY_ALIASES: dict[str, str] = {
    # English
    "cotton": "Cotton",
    "paddy": "Paddy(Common)",
    "rice": "Paddy(Common)",
    "groundnut": "Groundnut",
    "peanut": "Groundnut",
    "green gram": "Green Gram(Moong)(Whole)",
    "moong": "Green Gram(Moong)(Whole)",
    "toor": "Arhar(Tur/Red Gram)(Whole)",
    "arhar": "Arhar(Tur/Red Gram)(Whole)",
    "red gram": "Arhar(Tur/Red Gram)(Whole)",
    "chickpea": "Bengal Gram(Gram)(Whole)",
    "chana": "Bengal Gram(Gram)(Whole)",
    "bengal gram": "Bengal Gram(Gram)(Whole)",
    "gram": "Bengal Gram(Gram)(Whole)",
    "sunflower": "Sunflower/Sunflower Seed",
    "soybean": "Soyabean",
    "soya": "Soyabean",
    "urad": "Black Gram(Urd Beans)(Whole)",
    "black gram": "Black Gram(Urd Beans)(Whole)",
    "urd": "Black Gram(Urd Beans)(Whole)",
    "maize": "Maize",
    "corn": "Maize",
    "jowar": "Jowar(Sorghum)",
    "sorghum": "Jowar(Sorghum)",
    "mustard": "Mustard",
    "rapeseed": "Mustard",
    "sesame": "Sesamum(Sesame,Gingelly,Til)",
    "sesamum": "Sesamum(Sesame,Gingelly,Til)",
    "gingelly": "Sesamum(Sesame,Gingelly,Til)",
    "safflower": "Safflower",
    # Romanized Telugu / Hindi
    "pamuk": "Cotton",
    "patti": "Cotton",
    "vari": "Paddy(Common)",
    "verusenaga": "Groundnut",
    "verushanaga": "Groundnut",
    "verusha": "Groundnut",
    "veyyi": "Groundnut",
    "pesalu": "Green Gram(Moong)(Whole)",
    "kandi": "Arhar(Tur/Red Gram)(Whole)",
    "suryakanti": "Sunflower/Sunflower Seed",
    "minapappu": "Black Gram(Urd Beans)(Whole)",
    "makka": "Maize",
    "jonna": "Jowar(Sorghum)",
    "nuvvulu": "Sesamum(Sesame,Gingelly,Til)",
    "avise": "Sesamum(Sesame,Gingelly,Til)",
    # Telugu script
    "పత్తి": "Cotton",
    "వరి": "Paddy(Common)",
    "వేరుశనగ": "Groundnut",
    "వేరుసెనగ": "Groundnut",
    "పెసలు": "Green Gram(Moong)(Whole)",
    "కంది": "Arhar(Tur/Red Gram)(Whole)",
    "శనగ": "Bengal Gram(Gram)(Whole)",
    "సూర్యకాంతి": "Sunflower/Sunflower Seed",
    "సోయా": "Soyabean",
    "మినుములు": "Black Gram(Urd Beans)(Whole)",
    "మినప": "Black Gram(Urd Beans)(Whole)",
    "మొక్కజొన్న": "Maize",
    "జొన్న": "Jowar(Sorghum)",
    "నువ్వులు": "Sesamum(Sesame,Gingelly,Til)",
    "ఆవాలు": "Mustard",
}


def _detect_commodity(text: str, store) -> tuple[str | None, str | None]:
    """Return (commodity_name, group) or (None, None) if not found."""
    lower = text.lower()

    # Direct alias match
    for alias, canonical in _COMMODITY_ALIASES.items():
        if alias in lower:
            # Find the group from the store
            for group, commodities in store.commodities_by_group.items():
                if canonical in commodities:
                    return canonical, group
            return canonical, None

    # Try finding any exact commodity name from the dataset directly
    for group, commodities in store.commodities_by_group.items():
        for commodity in commodities:
            if commodity.lower() in lower:
                return commodity, group

    return None, None


async def _extract_commodity_llm(
    transcript_en: str, transcript_te: str, store
) -> tuple[str | None, str | None]:
    """
    LLM fallback: ask Llama which commodity the farmer meant.
    Handles Whisper hallucinations like 'book' for పత్తి (cotton).
    """
    all_commodities = [c for comms in store.commodities_by_group.values() for c in comms]
    commodity_list = ", ".join(all_commodities)

    prompt = (
        f"A farmer asked a voice question in Telugu. Speech recognition often makes errors with Telugu.\n\n"
        f"English transcript (may be wrong): \"{transcript_en}\"\n"
        f"Telugu transcript (may be wrong): \"{transcript_te}\"\n\n"
        f"Telugu crop name mappings (use these to interpret errors):\n"
        f"పత్తి=Cotton, వరి=Paddy(Common), వేరుశనగ=Groundnut, మొక్కజొన్న=Maize, "
        f"జొన్న=Jowar(Sorghum), కంది=Arhar(Tur/Red Gram)(Whole), పెసలు=Green Gram(Moong)(Whole), "
        f"మినుములు=Black Gram(Urd Beans)(Whole), నువ్వులు=Sesamum, సూర్యకాంతి=Sunflower\n\n"
        f"Common Whisper errors: పత్తి→'book'/'path'/'party', వరి→'worry'/'very'\n\n"
        f"Available commodities (reply with EXACT spelling from this list, or 'unknown'):\n"
        f"{commodity_list}"
    )

    try:
        client = AsyncGroq(api_key=settings.groq_api_key)
        resp = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0,
        )
        result = resp.choices[0].message.content.strip().strip("\"'.").strip()
        logger.info("LLM entity extraction: en=%r te=%r → %r", transcript_en, transcript_te, result)
    except Exception as exc:
        logger.warning("LLM entity extraction failed: %s", exc)
        return None, None

    if result.lower() == "unknown":
        return None, None

    # Exact match first
    for group, commodities in store.commodities_by_group.items():
        if result in commodities:
            return result, group

    # Case-insensitive fallback
    result_lower = result.lower()
    for group, commodities in store.commodities_by_group.items():
        for c in commodities:
            if c.lower() == result_lower:
                return c, group

    logger.warning("LLM returned %r but it matched no commodity in store", result)
    return None, None


# ---------------------------------------------------------------------------
# Groq Whisper STT helper
# ---------------------------------------------------------------------------
async def _transcribe_audio(audio_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Run Groq Whisper Large v3 on audio_bytes.
    Returns (transcript_te, transcript_en) — Telugu original + English translation.
    5-second timeout per call.
    """
    client = AsyncGroq(api_key=settings.groq_api_key)

    # Vocabulary hint — steers Whisper toward agricultural commodity words
    _PROMPT = (
        "పత్తి వరి వేరుశనగ గోధుమ మొక్కజొన్న జొన్న సజ్జ కంది పెసలు నువ్వులు ఆవాలు "
        "cotton paddy groundnut wheat maize jowar bajra toor moong sesame mustard sunflower"
    )

    te_task = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=(filename, io.BytesIO(audio_bytes)),
        language="te",
        prompt=_PROMPT,
        response_format="text",
    )
    en_task = client.audio.translations.create(
        model="whisper-large-v3",
        file=(filename, io.BytesIO(audio_bytes)),
        prompt=_PROMPT,
        response_format="text",
    )
    te_resp, en_resp = await asyncio.gather(te_task, en_task)
    transcript_te = str(te_resp).strip()
    transcript_en = str(en_resp).strip()

    return transcript_te, transcript_en


# ---------------------------------------------------------------------------
# ElevenLabs TTS helper
# ---------------------------------------------------------------------------
_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
_FALLBACK_AUDIO_DIR = Path(__file__).parent.parent.parent / "fallback"

_COMMODITY_FALLBACK: dict[str, str] = {
    "Cotton": "audio_cotton.mp3",
    "Paddy (Common)": "audio_paddy.mp3",
    "Groundnut": "audio_groundnut.mp3",
}


async def _text_to_speech(text: str, commodity: str | None) -> str | None:
    """
    Convert text to speech via ElevenLabs Multilingual v2.
    Returns base64-encoded MP3 string, or None on failure.
    Falls back to pre-generated MP3 if commodity matches one of the 3 fallbacks.
    5-second network timeout.
    """
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        logger.warning("ElevenLabs not configured — returning text-only response")
        return _load_fallback_audio(commodity)

    url = _ELEVENLABS_TTS_URL.format(voice_id=settings.elevenlabs_voice_id)
    payload = {
        "text": text,
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode()
    except Exception as exc:
        logger.warning("ElevenLabs TTS failed (%s) — attempting fallback audio", exc)
        return _load_fallback_audio(commodity)


def _load_fallback_audio(commodity: str | None) -> str | None:
    """Load a pre-generated MP3 from the fallback directory, or return None."""
    if commodity is None:
        return None
    filename = _COMMODITY_FALLBACK.get(commodity)
    if filename is None:
        return None
    path = _FALLBACK_AUDIO_DIR / filename
    if not path.exists():
        logger.warning("Fallback audio file not found: %s", path)
        return None
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except Exception as exc:
        logger.warning("Failed to read fallback audio: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Default advisory for unknown commodity
# ---------------------------------------------------------------------------
_DEFAULT_ADVISORY_TE = (
    "మీరు చెప్పిన పంట గురించి సమాచారం మాకు అందుబాటులో లేదు. "
    "దయచేసి పత్తి, వరి, లేదా వేరుశనగ గురించి అడగండి."
)


# ---------------------------------------------------------------------------
# POST /voice/transcribe — STT only
# ---------------------------------------------------------------------------
@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Speech-to-text only. Returns Telugu transcript + English translation.
    Does NOT run the advisory pipeline or TTS.
    """
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="STT service not configured.")

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    try:
        transcript_te, transcript_en = await _transcribe_audio(audio_bytes, audio.filename or "recording.webm")
    except Exception as exc:
        logger.exception("Whisper STT failed: %s", exc)
        raise HTTPException(status_code=502, detail="Speech recognition failed — please try again.")

    return JSONResponse({
        "transcript_te": transcript_te,
        "transcript_en": transcript_en,
    })


# ---------------------------------------------------------------------------
# POST /voice/query — Full voice pipeline
# ---------------------------------------------------------------------------
@router.post("/query")
async def voice_query(request: Request, audio: UploadFile = File(...)):
    """
    Full voice pipeline:
      1. Groq Whisper Large v3 STT  (Telugu → te text + en translation)
      2. Commodity entity extraction from English translation
      3. Single-call Llama 8B voice advisory in Telugu
      4. ElevenLabs Multilingual v2 TTS (5s timeout, falls back to text-only)

    Response:
    {
      "transcript_te": str,
      "transcript_en": str,
      "commodity_detected": str | null,
      "text_response_te": str,
      "audio_base64": str | null
    }
    """
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Voice service not configured.")

    # 1. Read audio bytes
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    # 2. STT
    try:
        transcript_te, transcript_en = await _transcribe_audio(
            audio_bytes, audio.filename or "recording.webm"
        )
    except Exception as exc:
        logger.exception("Whisper STT failed: %s", exc)
        raise HTTPException(status_code=502, detail="Speech recognition failed — please try again.")

    # 3. Entity extraction — string match first, then LLM fallback for Whisper hallucinations
    store = request.app.state.store
    commodity, group = _detect_commodity(transcript_en, store)
    if commodity is None:
        commodity, group = _detect_commodity(transcript_te, store)
    if commodity is None:
        commodity, group = await _extract_commodity_llm(transcript_en, transcript_te, store)
    logger.info("STT en=%r te=%r → commodity=%s", transcript_en, transcript_te, commodity)

    # 4. Advisory
    if commodity and group:
        records = store.series_by_key.get((group, commodity), [])
        try:
            advisory_te = await advise(commodity, group, records)
        except Exception as exc:
            logger.exception("Voice advisory LLM call failed: %s", exc)
            advisory_te = _DEFAULT_ADVISORY_TE
    else:
        advisory_te = _DEFAULT_ADVISORY_TE

    # 5. TTS (best-effort — never blocks a response)
    audio_base64: str | None = None
    try:
        audio_base64 = await _text_to_speech(advisory_te, commodity)
    except Exception as exc:
        logger.warning("TTS step raised unexpectedly: %s", exc)

    return JSONResponse({
        "transcript_te": transcript_te,
        "transcript_en": transcript_en,
        "commodity_detected": commodity,
        "text_response_te": advisory_te,
        "audio_base64": audio_base64,
    })


# ---------------------------------------------------------------------------
# GET /voice/advisory — advisory + TTS for a known commodity (used by quick-pick)
# ---------------------------------------------------------------------------
@router.get("/advisory")
async def voice_advisory(commodity: str, request: Request):
    """
    Skips STT. Runs advisory + TTS for a commodity the user selected manually.
    Used when Whisper failed to detect the crop from voice input.
    """
    store = request.app.state.store
    group = None
    for g, comms in store.commodities_by_group.items():
        if commodity in comms:
            group = g
            break

    if group is None:
        raise HTTPException(status_code=404, detail=f"Commodity not found: {commodity}")

    records = store.series_by_key.get((group, commodity), [])
    try:
        advisory_te = await advise(commodity, group, records)
    except Exception as exc:
        logger.exception("Advisory LLM failed: %s", exc)
        advisory_te = _DEFAULT_ADVISORY_TE

    audio_base64: str | None = None
    try:
        audio_base64 = await _text_to_speech(advisory_te, commodity)
    except Exception as exc:
        logger.warning("TTS failed: %s", exc)

    return JSONResponse({
        "transcript_te": "",
        "transcript_en": "",
        "commodity_detected": commodity,
        "text_response_te": advisory_te,
        "audio_base64": audio_base64,
    })


# ---------------------------------------------------------------------------
# POST /voice/chat — multi-turn conversational voice agent
# ---------------------------------------------------------------------------
@router.post("/chat")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    history: str = Form("[]"),
):
    """
    Conversational voice endpoint.
    Accepts audio + full conversation history (JSON array of {role, content}).
    Returns user transcript + Telugu reply + audio — caller appends both to history.

    Response:
    {
      "transcript":   str,         # What Whisper heard (show to user for correction)
      "reply_te":     str,         # Assistant Telugu response
      "audio_base64": str | null
    }
    """
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Voice service not configured.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    try:
        conversation = json.loads(history)
        if not isinstance(conversation, list):
            conversation = []
    except Exception:
        conversation = []

    # STT
    try:
        transcript_te, transcript_en = await _transcribe_audio(
            audio_bytes, audio.filename or "recording.webm"
        )
    except Exception as exc:
        logger.exception("Whisper STT failed: %s", exc)
        raise HTTPException(status_code=502, detail="Speech recognition failed.")

    # Use English transcript for LLM (more coherent) but show Telugu to user
    user_text = transcript_en or transcript_te

    # Build crop context for any commodities mentioned in history or transcript
    store = request.app.state.store
    commodity, group = _detect_commodity(transcript_en, store)
    if commodity is None:
        commodity, group = _detect_commodity(transcript_te, store)

    from agents.voice_chat import _build_context
    context = _build_context(store, commodity, group)

    # LLM conversational reply
    try:
        reply_te = await chat_respond(user_text, conversation, context)
    except Exception as exc:
        logger.exception("Chat LLM failed: %s", exc)
        reply_te = "క్షమించండి, ఇప్పుడు సమాధానం ఇవ్వలేకపోతున్నాను. మళ్ళీ ప్రయత్నించండి."

    # TTS — pass commodity=None so pre-generated fallback audio is never used.
    # The fallback MP3 has fixed content that won't match this dynamic reply.
    audio_base64: str | None = None
    try:
        audio_base64 = await _text_to_speech(reply_te, None)
    except Exception as exc:
        logger.warning("TTS failed: %s", exc)

    return JSONResponse({
        "transcript": transcript_te or transcript_en,
        "reply_te": reply_te,
        "audio_base64": audio_base64,
    })
