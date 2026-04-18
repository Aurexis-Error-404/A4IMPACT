"""
KrishiCFO · Live Mic Voice Test
Press ENTER to start recording, press ENTER again to stop.
Runs full pipeline: mic -> Whisper -> agents -> ElevenLabs -> plays audio.
"""

import os, sys, base64, asyncio, tempfile, threading
import numpy as np
import sounddevice as sd
import soundfile as sf

os.environ["PATH"] = (
    r"C:\Users\gouth\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
    + os.pathsep + os.environ.get("PATH", "")
)

GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_KEY      = os.getenv("ELEVENLABS_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

SAMPLE_RATE = 16000
SEASON_DATA = {
    "Cotton":    {"current_price": 7200, "msp": 6620, "msp_gap_pct":  8.8, "trend": "above MSP",      "season": "Kharif"},
    "Paddy":     {"current_price": 2180, "msp": 2300, "msp_gap_pct": -5.2, "trend": "below MSP",      "season": "Kharif"},
    "Groundnut": {"current_price": 5100, "msp": 5850, "msp_gap_pct":-12.8, "trend": "well below MSP", "season": "Kharif"},
}

# ── Record from mic ──────────────────────────────────────────────────────────
def record_mic() -> str:
    print("\n[MIC] Press ENTER to start recording...")
    input()
    print("[MIC] Recording... Press ENTER to stop.")

    frames = []
    stop_flag = threading.Event()

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback)
    stream.start()

    input()  # wait for second ENTER
    stream.stop()
    stream.close()

    audio = np.concatenate(frames, axis=0)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, SAMPLE_RATE)
    print(f"[MIC] Saved {len(audio)/SAMPLE_RATE:.1f}s of audio -> {tmp.name}")
    return tmp.name

# ── Stage 1: Whisper STT ─────────────────────────────────────────────────────
def transcribe(audio_path: str) -> str:
    print("\n[STT] Transcribing with Whisper medium...")
    import whisper
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, language="te")
    text = result["text"].strip()
    print(f"[STT] {text[:120]}")
    return text

# ── Stage 2: Entity extraction ───────────────────────────────────────────────
def extract_commodity(telugu_text: str) -> str:
    print("\n[ENTITY] Extracting commodity...")
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"""Extract commodity from this Telugu agricultural query.
Return ONLY one English word (Cotton, Paddy, Groundnut, Wheat, Maize). If unclear: Cotton.
Query: {telugu_text}
Commodity:"""}],
        max_tokens=10, temperature=0,
    )
    commodity = resp.choices[0].message.content.strip().split()[0]
    if commodity not in SEASON_DATA:
        commodity = "Cotton"
    print(f"[ENTITY] Detected: {commodity}")
    return commodity

# ── Stage 3: 3 parallel agents ───────────────────────────────────────────────
async def run_agent(role: str, instruction: str, commodity: str, data: dict) -> str:
    from groq import AsyncGroq
    c = AsyncGroq(api_key=GROQ_API_KEY, timeout=30.0)
    resp = await c.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"""You are a {role} analyzing {commodity}.
Price: Rs.{data['current_price']}/q, MSP: Rs.{data['msp']}/q, Gap: {data['msp_gap_pct']:+.1f}%, Season: {data['season']}.
{instruction}
One sentence verdict with price, gap, and action:"""}],
        max_tokens=80, temperature=0.3,
    )
    return resp.choices[0].message.content.strip()

async def get_advisory(commodity: str) -> str:
    print(f"\n[AGENTS] Running 3 parallel agents for {commodity}...")
    data = SEASON_DATA.get(commodity, SEASON_DATA["Cotton"])
    verdicts = await asyncio.gather(
        run_agent("Season-Optimist",  "Find upside signals and reasons to hold.", commodity, data),
        run_agent("Season-Pessimist", "Find downside risks and reasons to sell now.", commodity, data),
        run_agent("Risk Analyst",     "Assess MSP proximity risk and give balanced action.", commodity, data),
    )
    print(f"  Optimist  : {verdicts[0][:80]}")
    print(f"  Pessimist : {verdicts[1][:80]}")
    print(f"  Risk      : {verdicts[2][:80]}")

    from groq import Groq
    synth = Groq(api_key=GROQ_API_KEY).chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"""Synthesize into a 2-sentence Telugu-friendly advisory for {commodity}.
Mention: commodity, MSP gap, one clear action (hold/sell/wait).
Verdicts: 1.{verdicts[0]} 2.{verdicts[1]} 3.{verdicts[2]}
Advisory:"""}],
        max_tokens=100, temperature=0.2, timeout=30,
    )
    advisory = synth.choices[0].message.content.strip()
    print(f"\n[ADVISORY] {advisory}")
    return advisory

# ── Stage 4: ElevenLabs TTS + playback ───────────────────────────────────────
def speak(advisory_text: str):
    print("\n[TTS] Generating audio with ElevenLabs...")
    import httpx
    resp = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
        json={"text": advisory_text, "model_id": "eleven_multilingual_v2"},
        timeout=10,
    )
    resp.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(resp.content)
    tmp.close()
    print(f"[TTS] {len(resp.content)/1024:.1f} KB — playing now...")

    # Play via ffplay (comes with ffmpeg)
    os.system(f'ffplay -nodisp -autoexit "{tmp.name}" 2>nul')

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("  KrishiCFO · Live Mic Test")
    print("  Speak a Telugu commodity question")
    print("=" * 56)

    audio_path = record_mic()
    telugu_text = transcribe(audio_path)
    commodity   = extract_commodity(telugu_text)
    advisory    = asyncio.run(get_advisory(commodity))
    speak(advisory)

    print("\n[DONE] Full loop complete.")

if __name__ == "__main__":
    main()
