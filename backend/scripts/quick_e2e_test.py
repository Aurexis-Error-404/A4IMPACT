"""Quick end-to-end test of /voice/chat — sends a real audio file and checks the response."""
import asyncio
import base64
import io
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    import httpx
    from pathlib import Path

    fallback = Path(__file__).parent.parent / "fallback" / "audio_cotton.mp3"
    if not fallback.exists():
        print("ERROR: fallback/audio_cotton.mp3 not found")
        return

    audio_bytes = fallback.read_bytes()
    print(f"Sending {len(audio_bytes):,} bytes to /voice/chat ...")

    t0 = time.time()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "http://localhost:8000/voice/chat",
            files={"audio": ("recording.mp3", io.BytesIO(audio_bytes), "audio/mpeg")},
            data={"history": "[]"},
        )
    elapsed = time.time() - t0

    print(f"\nHTTP {resp.status_code} in {elapsed:.1f}s")
    if resp.status_code != 200:
        print(f"Body: {resp.text[:500]}")
        return

    data = resp.json()
    print(f"transcript:   {data.get('transcript', '?')[:100]}")
    print(f"reply_te:     {data.get('reply_te', '?')[:100]}")

    audio_b64 = data.get("audio_base64")
    if audio_b64:
        decoded = base64.b64decode(audio_b64)
        print(f"audio_base64: PRESENT ({len(audio_b64)} chars, {len(decoded):,} bytes decoded)")
        is_mp3 = decoded[:3] == b"ID3" or decoded[:2] == b"\xff\xfb"
        print(f"is_mp3:       {is_mp3}")
        print("✅ SUCCESS — audio returned!")
    else:
        print("audio_base64: NULL")
        print("❌ STILL FAILING — no audio returned")

if __name__ == "__main__":
    asyncio.run(main())
