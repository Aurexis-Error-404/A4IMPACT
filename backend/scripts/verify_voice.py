"""
verify_voice.py — Phase 6 voice pipeline verification.

Run from backend/ with the venv active:
    python scripts/verify_voice.py

Tests:
  1. Config   — ElevenLabs keys are loaded from .env
  2. TTS      — ElevenLabs returns audio for a short Telugu sentence
  3. Groq STT — Whisper is reachable (model list check, no audio file needed)
  4. Advisory — voice_advisory.py LLM call returns Telugu text
  5. HTTP     — POST /voice/query is reachable (requires server running on :8000)
"""

import asyncio
import base64
import os
import sys
import time

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# Make sure we're running from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────
def ok(msg):  print(f"  \033[32m✓\033[0m  {msg}")
def fail(msg): print(f"  \033[31m✗\033[0m  {msg}")
def info(msg): print(f"  \033[34m·\033[0m  {msg}")
def header(msg): print(f"\n\033[1m{msg}\033[0m")


# ─────────────────────────────────────────────────────────────
# 1. Config check
# ─────────────────────────────────────────────────────────────
def check_config():
    header("1 · Config — ElevenLabs keys in .env")
    from config import Settings
    s = Settings()
    if s.groq_api_key:
        ok(f"GROQ_API_KEY      present (starts with {s.groq_api_key[:10]}…)")
    else:
        fail("GROQ_API_KEY      MISSING — add it to backend/.env")

    if s.elevenlabs_api_key:
        ok(f"ELEVENLABS_API_KEY present (starts with {s.elevenlabs_api_key[:8]}…)")
    else:
        fail("ELEVENLABS_API_KEY MISSING — add it to backend/.env")

    if s.elevenlabs_voice_id:
        ok(f"ELEVENLABS_VOICE_ID present ({s.elevenlabs_voice_id})")
    else:
        fail("ELEVENLABS_VOICE_ID MISSING — add it to backend/.env")

    return s


# ─────────────────────────────────────────────────────────────
# 2. ElevenLabs TTS
# ─────────────────────────────────────────────────────────────
async def check_tts(s):
    header("2 · ElevenLabs TTS — convert short Telugu text → audio")
    import httpx

    TEST_TEXT = "పత్తి ధర ఈ సీజన్‌లో పెరుగుతోంది. హోల్డ్ చేయండి."
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{s.elevenlabs_voice_id}"
    payload = {
        "text": TEST_TEXT,
        "model_id": "eleven_v3",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": s.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        elapsed = time.time() - t0

        if resp.status_code == 200:
            audio_bytes = resp.content
            b64 = base64.b64encode(audio_bytes).decode()
            ok(f"TTS success — {len(audio_bytes):,} bytes audio in {elapsed:.1f}s")
            ok(f"base64 preview: {b64[:40]}…")
            # Save to temp so you can listen
            out_path = os.path.join(os.path.dirname(__file__), "tts_test_output.mp3")
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            ok(f"Saved test audio → {out_path}")
        elif resp.status_code == 401:
            fail(f"TTS 401 Unauthorized — check ELEVENLABS_API_KEY")
        elif resp.status_code == 422:
            fail(f"TTS 422 — bad voice_id '{s.elevenlabs_voice_id}'? Body: {resp.text[:200]}")
        else:
            fail(f"TTS HTTP {resp.status_code}: {resp.text[:200]}")
    except httpx.TimeoutException:
        fail("TTS timed out after 10s — check network / ElevenLabs status")
    except Exception as exc:
        fail(f"TTS error: {exc}")


# ─────────────────────────────────────────────────────────────
# 3. Groq Whisper reachability (model list)
# ─────────────────────────────────────────────────────────────
async def check_groq_whisper(s):
    header("3 · Groq Whisper — API reachability check")
    import httpx

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {s.groq_api_key}"},
            )
        if resp.status_code == 200:
            models = [m["id"] for m in resp.json().get("data", [])]
            whisper_models = [m for m in models if "whisper" in m.lower()]
            if whisper_models:
                ok(f"Whisper models available: {', '.join(whisper_models)}")
            else:
                info("No whisper models returned — may still work, but double-check")
        else:
            fail(f"Groq models API returned {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        fail(f"Groq API unreachable: {exc}")


# ─────────────────────────────────────────────────────────────
# 4. Voice advisory LLM call
# ─────────────────────────────────────────────────────────────
async def check_advisory():
    header("4 · Voice Advisory — single Llama 8B Telugu advisory call")
    from agents.voice_advisory import advise
    from data.loader import load
    from config import Settings

    s = Settings()
    store = load(s.data_path)

    # Pick Cotton for the test
    group = "Fibre Crops"
    commodity = "Cotton"
    records = store.series_by_key.get((group, commodity), [])

    if not records:
        fail("No Cotton records found in dataset — check DATA_PATH")
        return

    info(f"Calling advisory for {commodity} ({len(records)} seasons)…")
    t0 = time.time()
    try:
        advisory = await advise(commodity, group, records)
        elapsed = time.time() - t0
        ok(f"Advisory returned in {elapsed:.1f}s")
        ok(f"Telugu text: {advisory[:120]}{'…' if len(advisory) > 120 else ''}")
    except Exception as exc:
        fail(f"Advisory call failed: {exc}")


# ─────────────────────────────────────────────────────────────
# 5. HTTP smoke test (requires server on :8000)
# ─────────────────────────────────────────────────────────────
async def check_http_endpoint():
    header("5 · HTTP — POST /voice/query endpoint reachable?")
    import httpx

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:8000/health")
        if resp.status_code == 200:
            ok("Server is running on :8000")
            info("To test /voice/query end-to-end, use the UI VoiceButton or:")
            info('  curl -X POST http://localhost:8000/voice/query -F "audio=@path/to/audio.webm"')
        else:
            info(f"Server responded {resp.status_code} on /health — is it fully loaded?")
    except httpx.ConnectError:
        info("Server not running on :8000 — start it, then re-run this script")
        info("  cd backend && .venv\\Scripts\\uvicorn main:app --reload --port 8000")


# ─────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────
async def main():
    print("\n" + "═" * 55)
    print("  KrishiCFO · Phase 6 Voice Pipeline Verification")
    print("═" * 55)

    s = check_config()
    await check_tts(s)
    await check_groq_whisper(s)
    await check_advisory()
    await check_http_endpoint()

    print("\n" + "═" * 55)
    print("  Done. Fix any ✗ above before the demo.")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
