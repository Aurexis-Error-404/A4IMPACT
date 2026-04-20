"""
deep_voice_test.py — Deep diagnostic of the voice pipeline.
Tests each failure mode independently and reports exactly where audio is lost.
"""

import asyncio
import base64
import io
import os
import sys
import time
import traceback

# Force UTF-8 output on Windows
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ok(msg):  print(f"  \033[32m✓\033[0m  {msg}")
def fail(msg): print(f"  \033[31m✗\033[0m  {msg}")
def info(msg): print(f"  \033[34m·\033[0m  {msg}")
def warn(msg): print(f"  \033[33m⚠\033[0m  {msg}")
def header(msg): print(f"\n\033[1m{'─'*55}\n{msg}\n{'─'*55}\033[0m")


async def main():
    print("\n" + "═" * 60)
    print("  KrishiCFO · Deep Voice Pipeline Diagnostic")
    print("═" * 60)

    from config import Settings
    s = Settings()
    issues = []

    # ──────────────────────────────────────────────
    # 1. ENV CONFIG CHECK
    # ──────────────────────────────────────────────
    header("1 · Environment Configuration")
    if s.groq_api_key:
        ok(f"GROQ_API_KEY present ({s.groq_api_key[:12]}…)")
    else:
        fail("GROQ_API_KEY MISSING")
        issues.append("GROQ_API_KEY not set")

    if s.elevenlabs_api_key:
        ok(f"ELEVENLABS_API_KEY present ({s.elevenlabs_api_key[:10]}…)")
    else:
        fail("ELEVENLABS_API_KEY MISSING")
        issues.append("ELEVENLABS_API_KEY not set")

    if s.elevenlabs_voice_id:
        ok(f"ELEVENLABS_VOICE_ID = {s.elevenlabs_voice_id}")
    else:
        fail("ELEVENLABS_VOICE_ID MISSING")
        issues.append("ELEVENLABS_VOICE_ID not set")

    # ──────────────────────────────────────────────
    # 2. ELEVENLABS TTS — multiple tests
    # ──────────────────────────────────────────────
    header("2 · ElevenLabs TTS — Reliability (3 sequential calls)")
    import httpx

    test_texts = [
        "పత్తి ధర ఈ సీజన్‌లో పెరుగుతోంది.",
        "మీరు ఇప్పుడు అమ్మకం చేయడం మేలు. వరి ధర MSP కంటే తక్కువగా ఉంది.",
        "వేరుశనగ ధర ప్రస్తుతం Rs.5,100 ఉంది. MSP Rs.5,850 కంటే 12.8% తక్కువ. ఆగి ధరలు పెరిగిన తర్వాత అమ్మండి.",
    ]

    tts_successes = 0
    tts_failures = 0

    for i, text in enumerate(test_texts, 1):
        info(f"Test {i}/3: {text[:50]}…")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{s.elevenlabs_voice_id}"
        payload = {
            "text": text,
            "model_id": "eleven_v3",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        headers_dict = {
            "xi-api-key": s.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        try:
            t0 = time.time()
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers_dict)
            elapsed = time.time() - t0

            if resp.status_code == 200:
                audio_bytes = resp.content
                content_type = resp.headers.get("content-type", "?")
                b64 = base64.b64encode(audio_bytes).decode()

                # Validate the audio content
                is_mp3 = audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb"
                is_valid_b64 = len(b64) > 100

                if is_mp3 and is_valid_b64:
                    ok(f"TTS OK — {len(audio_bytes):,}B, {elapsed:.1f}s, content-type={content_type}")
                    tts_successes += 1
                else:
                    warn(f"TTS returned {resp.status_code} but content looks wrong:")
                    warn(f"  First 20 bytes hex: {audio_bytes[:20].hex()}")
                    warn(f"  Content-Type: {content_type}")
                    warn(f"  Is MP3: {is_mp3}, Base64 len: {len(b64)}")
                    tts_failures += 1
            elif resp.status_code == 401:
                fail(f"TTS 401 Unauthorized — API key invalid")
                issues.append("ElevenLabs API key invalid (401)")
                tts_failures += 1
            elif resp.status_code == 422:
                fail(f"TTS 422 — voice_id '{s.elevenlabs_voice_id}' invalid? Body: {resp.text[:200]}")
                issues.append(f"ElevenLabs voice_id invalid (422): {resp.text[:100]}")
                tts_failures += 1
            elif resp.status_code == 429:
                fail(f"TTS 429 Rate Limited — ElevenLabs quota exhausted")
                issues.append("ElevenLabs rate limited (429) — quota may be exhausted")
                tts_failures += 1
            else:
                fail(f"TTS HTTP {resp.status_code}: {resp.text[:200]}")
                issues.append(f"ElevenLabs returned {resp.status_code}")
                tts_failures += 1
        except httpx.TimeoutException:
            fail(f"TTS timed out after 15s")
            issues.append("ElevenLabs TTS timeout")
            tts_failures += 1
        except Exception as exc:
            fail(f"TTS error: {exc}")
            issues.append(f"ElevenLabs error: {exc}")
            tts_failures += 1

        # Small delay between calls
        await asyncio.sleep(0.5)

    info(f"TTS results: {tts_successes}/3 succeeded, {tts_failures}/3 failed")
    if tts_failures > 0:
        issues.append(f"ElevenLabs TTS intermittent failures: {tts_failures}/3 failed")

    # ──────────────────────────────────────────────
    # 3. TEST THE _text_to_speech() FUNCTION DIRECTLY
    # ──────────────────────────────────────────────
    header("3 · Backend _text_to_speech() function — direct test")
    try:
        from routers.voice import _text_to_speech
        test_text = "పత్తి ధర MSP కంటే ఎక్కువగా ఉంది. అమ్మకం సరైన నిర్ణయం."

        t0 = time.time()
        result = await _text_to_speech(test_text, "Cotton")
        elapsed = time.time() - t0

        if result is None:
            fail("_text_to_speech returned None — audio will be missing in response!")
            # Check why
            if not s.elevenlabs_api_key or not s.elevenlabs_voice_id:
                fail("  Reason: ElevenLabs not configured in Settings")
                issues.append("_text_to_speech returns None because config is missing")
            else:
                fail("  Reason: ElevenLabs call failed, and fallback audio also failed/missing")
                issues.append("_text_to_speech returns None — TTS call failed, no working fallback")
        elif isinstance(result, str) and len(result) > 100:
            ok(f"_text_to_speech returned base64 string ({len(result)} chars) in {elapsed:.1f}s")

            # Validate it decodes to real audio
            try:
                decoded = base64.b64decode(result)
                is_mp3 = decoded[:3] == b"ID3" or decoded[:2] == b"\xff\xfb"
                ok(f"  Decoded to {len(decoded):,} bytes, is_mp3={is_mp3}")
            except Exception as e:
                fail(f"  Base64 decode failed: {e}")
                issues.append("_text_to_speech returns invalid base64")
        else:
            warn(f"_text_to_speech returned unexpected: type={type(result)}, len={len(str(result))}")

    except Exception as exc:
        fail(f"_text_to_speech raised: {exc}")
        traceback.print_exc()
        issues.append(f"_text_to_speech exception: {exc}")

    # ──────────────────────────────────────────────
    # 4. FALLBACK AUDIO CHECK
    # ──────────────────────────────────────────────
    header("4 · Fallback audio files")
    from pathlib import Path
    fallback_dir = Path(__file__).parent.parent.parent / "fallback"
    info(f"Fallback directory: {fallback_dir}")
    if fallback_dir.exists():
        for f in fallback_dir.iterdir():
            if f.suffix == ".mp3":
                size = f.stat().st_size
                b64_len = len(base64.b64encode(f.read_bytes()).decode())
                ok(f"  {f.name}: {size:,} bytes → {b64_len} chars base64")
    else:
        warn("Fallback directory does not exist")

    # ──────────────────────────────────────────────
    # 5. END-TO-END: /voice/chat endpoint test
    # ──────────────────────────────────────────────
    header("5 · HTTP /voice/chat endpoint — end-to-end test")
    try:
        # Check if server is running
        async with httpx.AsyncClient(timeout=3.0) as client:
            health = await client.get("http://localhost:8000/health")

        if health.status_code != 200:
            warn("Server not healthy — skipping endpoint test")
        else:
            ok("Server is running on :8000")

            # Use a fallback audio file as test input
            test_audio_path = fallback_dir / "audio_cotton.mp3"
            if test_audio_path.exists():
                info("Sending audio_cotton.mp3 to /voice/chat …")
                audio_bytes = test_audio_path.read_bytes()

                form_data = {
                    "history": (None, "[]"),
                }
                files = {
                    "audio": ("recording.mp3", io.BytesIO(audio_bytes), "audio/mpeg"),
                }

                t0 = time.time()
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "http://localhost:8000/voice/chat",
                        files=files,
                        data={"history": "[]"},
                    )
                elapsed = time.time() - t0

                if resp.status_code == 200:
                    data = resp.json()
                    ok(f"Response received in {elapsed:.1f}s")
                    info(f"  transcript:    {data.get('transcript', '?')[:80]}")
                    info(f"  reply_te:      {data.get('reply_te', '?')[:80]}")

                    audio_b64 = data.get("audio_base64")
                    if audio_b64:
                        ok(f"  audio_base64:  PRESENT ({len(audio_b64)} chars)")
                        # Validate
                        try:
                            decoded = base64.b64decode(audio_b64)
                            is_mp3 = decoded[:3] == b"ID3" or decoded[:2] == b"\xff\xfb"
                            ok(f"  Decoded audio: {len(decoded):,} bytes, is_mp3={is_mp3}")
                        except Exception as e:
                            fail(f"  Audio base64 decode failed: {e}")
                            issues.append("Endpoint returns bad base64 audio")
                    else:
                        fail("  audio_base64:  NULL — ⚠ THIS IS THE BUG!")
                        fail("  The endpoint returned Telugu text but NO audio data.")
                        issues.append("CRITICAL: /voice/chat returned null audio_base64")
                elif resp.status_code == 502:
                    fail(f"  502 — STT (Whisper) failed on this audio")
                    issues.append("/voice/chat returned 502 — Whisper STT failure")
                else:
                    fail(f"  HTTP {resp.status_code}: {resp.text[:200]}")
                    issues.append(f"/voice/chat returned {resp.status_code}")
            else:
                warn("No test audio file — can't test endpoint end-to-end")

    except httpx.ConnectError:
        info("Server not running on :8000 — skipping endpoint test")
        info("Start it: cd backend && .venv\\Scripts\\uvicorn main:app --reload --port 8000")

    # ──────────────────────────────────────────────
    # 6. CHECK CODE ISSUES (static analysis)
    # ──────────────────────────────────────────────
    header("6 · Code-level issue scan")

    # Check the TTS function for known bug patterns
    from routers import voice as voice_module
    import inspect
    source = inspect.getsource(voice_module._text_to_speech)

    # Check timeout
    if "timeout=5.0" in source:
        fail("_text_to_speech uses 5s timeout — TOO SHORT for Telugu TTS!")
        issues.append("TTS timeout too short (5s)")
    elif "timeout=15.0" in source:
        ok("_text_to_speech uses 15s timeout")
    else:
        import re
        timeout_match = re.search(r"timeout=(\d+\.?\d*)", source)
        if timeout_match:
            info(f"_text_to_speech uses {timeout_match.group(1)}s timeout")
        else:
            warn("Could not detect timeout value in _text_to_speech")

    # Check if the function swallows errors silently
    if "return _load_fallback_audio" in source:
        info("_text_to_speech falls back to pre-generated audio on failure")

    # Check voice_chat _text_to_speech call — commodity=None means NO fallback
    chat_source = inspect.getsource(voice_module.voice_chat)
    if '_text_to_speech(reply_te, None)' in chat_source:
        warn("voice_chat passes commodity=None to _text_to_speech →")
        warn("  If ElevenLabs fails, fallback audio is NEVER loaded (by design)")
        warn("  This means: if TTS times out → NO audio at all!")
        issues.append("DESIGN ISSUE: /voice/chat passes None commodity → no fallback possible")

    # Check playAudio in the frontend
    info("Frontend: playAudio uses 'data:audio/mp3;base64,' prefix")
    info("  ↳ This is correct for ElevenLabs MP3 output")

    # ──────────────────────────────────────────────
    # 7. GROQ WHISPER STT CHECK
    # ──────────────────────────────────────────────
    header("7 · Groq Whisper STT — reachability + model check")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {s.groq_api_key}"},
            )
        if resp.status_code == 200:
            models = [m["id"] for m in resp.json().get("data", [])]
            whisper = [m for m in models if "whisper" in m.lower()]
            ok(f"Groq API reachable. Whisper models: {', '.join(whisper)}")
        else:
            fail(f"Groq API returned {resp.status_code}")
            issues.append(f"Groq API error: {resp.status_code}")
    except Exception as exc:
        fail(f"Groq API unreachable: {exc}")
        issues.append(f"Groq API unreachable: {exc}")

    # ──────────────────────────────────────────────
    # 8. CHECK ELEVENLABS QUOTA
    # ──────────────────────────────────────────────
    header("8 · ElevenLabs account quota check")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": s.elevenlabs_api_key},
            )
        if resp.status_code == 200:
            sub = resp.json()
            char_limit = sub.get("character_limit", "?")
            char_used = sub.get("character_count", "?")
            tier = sub.get("tier", "?")
            ok(f"Tier: {tier}")
            ok(f"Characters used: {char_used:,} / {char_limit:,}")
            remaining = char_limit - char_used if isinstance(char_limit, int) and isinstance(char_used, int) else None
            if remaining is not None:
                if remaining < 500:
                    fail(f"Only {remaining} characters remaining! TTS will fail soon!")
                    issues.append(f"CRITICAL: Only {remaining} ElevenLabs characters remaining")
                elif remaining < 5000:
                    warn(f"{remaining:,} characters remaining — getting low")
                    issues.append(f"WARNING: Only {remaining:,} ElevenLabs characters remaining")
                else:
                    ok(f"{remaining:,} characters remaining")
        elif resp.status_code == 401:
            fail("ElevenLabs API key invalid (401)")
            issues.append("ElevenLabs API key invalid")
        else:
            warn(f"Could not check quota: {resp.status_code}")
    except Exception as exc:
        warn(f"Could not check ElevenLabs quota: {exc}")

    # ──────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────
    print("\n" + "═" * 60)
    if issues:
        print(f"  \033[31m{len(issues)} ISSUE(S) FOUND:\033[0m")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
    else:
        print("  \033[32mNo issues found — pipeline looks healthy.\033[0m")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
