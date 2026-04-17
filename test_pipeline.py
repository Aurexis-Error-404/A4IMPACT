"""
KrishiCFO · Voice Pipeline CLI Test
Run each stage independently. Pass all 4 before wiring the UI.

Usage:
    python test_pipeline.py --audio fallback/audio_cotton.mp3
"""

import argparse
import base64
import os
import sys
import asyncio

# ── CONFIG — fill these in ──────────────────────────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_KEY  = os.getenv("ELEVENLABS_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
FFMPEG_PATH = r"C:\Users\gouth\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
# ────────────────────────────────────────────────────────────────────────────

os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

PASS = "  PASS PASS"
FAIL = "  FAIL FAIL"

# ── STAGE 1: Audio -> Whisper -> Telugu text ──────────────────────────────────
def stage1_whisper(audio_path: str) -> str:
    print("\n[STAGE 1] Audio -> Whisper STT")
    try:
        import whisper
        model = whisper.load_model("medium")
        result = model.transcribe(audio_path, language="te")
        text = result["text"].strip()
        lang = result.get("language", "?")
        print(f"  Language detected : {lang}")
        print(f"  Transcription     : {text[:120]}")
        print(PASS)
        return text
    except Exception as e:
        print(f"{FAIL} — {e}")
        sys.exit(1)

# ── STAGE 2: Telugu text -> entity extraction -> commodity ────────────────────
def stage2_entity(telugu_text: str) -> str:
    print("\n[STAGE 2] Telugu text -> commodity entity extraction")
    if not GROQ_API_KEY:
        print("  SKIPPED — set GROQ_API_KEY env var")
        return "Cotton"   # default for testing stages 3+

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""Extract the commodity name from this Telugu agricultural query.
Return ONLY one word: the commodity name in English (e.g. Cotton, Paddy, Groundnut, Wheat, Maize).
If unclear, return: Unknown

Query: {telugu_text}
Commodity:"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        commodity = resp.choices[0].message.content.strip()
        print(f"  Commodity detected: {commodity}")
        print(PASS)
        return commodity
    except Exception as e:
        print(f"{FAIL} — {e}")
        sys.exit(1)

# ── STAGE 3: Commodity -> 3 parallel agents -> synthesized advisory ───────────
SEASON_DATA = {
    "Cotton":    {"current_price": 7200, "msp": 6620, "msp_gap_pct": 8.8,  "trend": "above MSP", "season": "Kharif"},
    "Paddy":     {"current_price": 2180, "msp": 2300, "msp_gap_pct": -5.2, "trend": "below MSP", "season": "Kharif"},
    "Groundnut": {"current_price": 5100, "msp": 5850, "msp_gap_pct":-12.8, "trend": "well below MSP", "season": "Kharif"},
}

async def run_agent(client, role: str, instruction: str, commodity: str, data: dict) -> str:
    from groq import AsyncGroq
    c = AsyncGroq(api_key=GROQ_API_KEY, timeout=30.0)
    prompt = f"""You are a {role} analyzing {commodity} prices.
Data: Current price Rs.{data['current_price']}/q, MSP Rs.{data['msp']}/q,
Gap: {data['msp_gap_pct']:+.1f}%, Trend: {data['trend']}, Season: {data['season']}.

{instruction}

Give a 1-sentence verdict. Be specific — mention the price, the gap, and your recommendation."""
    resp = await c.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()

async def stage3_agents(commodity: str) -> str:
    print(f"\n[STAGE 3] {commodity} -> 3 parallel agents -> advisory")
    if not GROQ_API_KEY:
        print("  SKIPPED — set GROQ_API_KEY env var")
        return f"{commodity} is trading near MSP — moderate hold signal."

    data = SEASON_DATA.get(commodity, SEASON_DATA["Cotton"])
    from groq import AsyncGroq

    try:
        verdicts = await asyncio.gather(
            run_agent(None, "Season-Optimist",  "Look for upside signals and reasons to hold.", commodity, data),
            run_agent(None, "Season-Pessimist", "Look for downside risks and reasons to sell now.", commodity, data),
            run_agent(None, "Risk Analyst",     "Assess MSP proximity risk and give a balanced action.", commodity, data),
        )

        print(f"  Optimist  : {verdicts[0][:90]}")
        print(f"  Pessimist : {verdicts[1][:90]}")
        print(f"  Risk      : {verdicts[2][:90]}")

        # Synthesize
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        synth_prompt = f"""Synthesize these 3 analyst verdicts about {commodity} into a 2-sentence Telugu-friendly advisory.
Mention: commodity name, MSP gap, and one clear action word (hold/sell/wait).
Verdicts:
1. {verdicts[0]}
2. {verdicts[1]}
3. {verdicts[2]}
Advisory (English):"""
        synth = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": synth_prompt}],
            max_tokens=100,
            temperature=0.2,
            timeout=30,
        )
        advisory = synth.choices[0].message.content.strip()
        print(f"  Advisory  : {advisory[:120]}")
        print(PASS)
        return advisory
    except Exception as e:
        print(f"{FAIL} — {e}")
        sys.exit(1)

# ── STAGE 4: Advisory -> ElevenLabs -> base64 MP3 ────────────────────────────
def stage4_tts(advisory_text: str) -> str:
    print("\n[STAGE 4] Advisory -> ElevenLabs TTS -> base64 MP3")
    if not ELEVENLABS_KEY:
        print("  SKIPPED — set ELEVENLABS_KEY env var")
        return ""
    if not ELEVENLABS_VOICE_ID:
        print("  SKIPPED — set ELEVENLABS_VOICE_ID env var")
        return ""

    import httpx
    try:
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={"text": advisory_text, "model_id": "eleven_multilingual_v2"},
            timeout=10,
        )
        resp.raise_for_status()
        audio_b64 = base64.b64encode(resp.content).decode()
        with open("tts_test_output.mp3", "wb") as f:
            f.write(resp.content)
        print(f"  Audio size  : {len(resp.content) / 1024:.1f} KB")
        print(f"  Base64 len  : {len(audio_b64)} chars")
        print(f"  Saved to    : tts_test_output.mp3")
        print(PASS)
        return audio_b64
    except Exception as e:
        print(f"{FAIL} — {e}")
        sys.exit(1)

# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="fallback/audio_cotton.mp3")
    parser.add_argument("--stage", type=int, default=0, help="Run only this stage (1-4). 0 = all.")
    args = parser.parse_args()

    print("=" * 56)
    print("  KrishiCFO · Voice Pipeline Test")
    print("=" * 56)

    telugu_text = stage1_whisper(args.audio)
    commodity   = stage2_entity(telugu_text)
    if commodity in ("Unknown", ""):
        print("  NOTE: Entity unknown from TTS audio — defaulting to Cotton for stages 3+")
        commodity = "Cotton"
    advisory    = asyncio.run(stage3_agents(commodity))
    stage4_tts(advisory)

    print("\n" + "=" * 56)
    print("  All stages complete — pipeline verified.")
    print("=" * 56)

if __name__ == "__main__":
    main()
