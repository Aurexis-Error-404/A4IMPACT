# KrishiCFO · Member C · Voice + Pitch · 24h Plan

**Role:** Voice Pipeline + Pitch Lead  
**Stack:** WhisperFlow (STT) · ElevenLabs Multilingual v2 (TTS)  
**Targets:** `<3s` text response · `<7s` audio response

---

## Voice Architecture (5 Stages, ~3.8s total)

| # | Stage | Detail | Time |
|---|-------|---------|------|
| 01 | Browser MediaRecorder | Captures Telugu audio, POSTs WAV to `/voice/query` as multipart/form-data | — |
| 02 | WhisperFlow STT | OpenAI Whisper with `language="te"` + Llama 8B translation to English | ~0.8s |
| 03 | 3× Llama 8B Parallel | Season-Optimist + Season-Pessimist + Risk Analyst via `asyncio.gather()` | ~1.4s |
| 04 | Llama 8B Synthesizer | Merges 3 verdicts into 2–3 sentence Telugu advisory | ~0.7s |
| 05 | ElevenLabs Multilingual v2 | Telugu text → audio bytes → base64. 5s timeout; fallback to text-only | ~0.9s |

> Text arrives first (~3s). Audio plays when ready (~7s). Always display text while audio loads.

---

## Hour-by-Hour Roadmap

### Hour 0–2 · Insurance First, Scaffold Second

- [ ] **Pre-generate 3 Telugu audio clips** (ElevenLabs web playground — before writing any code)
  - `fallback/audio_cotton.mp3` — high MSP deviation scenario
  - `fallback/audio_paddy.mp3` — moderate scenario
  - `fallback/audio_groundnut.mp3` — risk scenario
- [ ] **Select and lock voice_id** — test Telugu prosody at elevenlabs.io, note voice_id into `config.py`
- [ ] **Scaffold `VoiceButton.tsx`** — UI states only (mock backend, 2s delay):
  - `idle` → `recording` → `processing` → `response`
  - Use `navigator.mediaDevices.getUserMedia()` + WAV encoding
  - Design: `--bg:#0f120e`, `--gold:#ef9f27`, Martian Mono labels
- [ ] **Verify WhisperFlow access** — curl test with a sample Telugu audio file; confirm `language="te"` returns legible output

### Hour 2–6 · VoiceButton Full Integration

- [ ] **Complete `VoiceButton.tsx`** with real MediaRecorder logic
  - Collect blobs → `Blob({ type: 'audio/wav' })` → `FormData.append('audio', blob, 'recording.wav')`
  - POST to `/voice/query` — do NOT set Content-Type manually
  - Handle: mic denied, no-mic device, network error
- [ ] **Wire audio playback from base64**
  - `new Audio('data:audio/mp3;base64,' + data.audio_base64).play()`
  - Show `text_response_te` immediately — don't wait for audio
  - Add "Replay" button; pause/reset on new query

### Hour 6–10 · Voice Loop End-to-End

- [ ] **CLI pipeline test** — validate each stage in isolation before chaining:
  1. Audio → Whisper → Telugu text ✓
  2. Telugu text → entity extraction → commodity name ✓
  3. Commodity → 3 agents → synthesized advisory ✓
  4. Advisory → ElevenLabs → base64 MP3 ✓
- [ ] **Wire `VoiceButton.tsx` to Member A's `/voice/query`** — replace mock with real endpoint
  - Response shape: `{ text_response_te, audio_base64, commodity_detected }`
  - If `audio_base64` is null: show text-only with small indicator
  - If request fails: show "Voice query failed — please try again"

**Milestone (Hour 10):** Telugu speech → Telugu text in <3s; audio in <7s or text-only fallback works; all error states handled without crashing.

### Hour 10–14 · Integration + Audio UX

- [ ] **Test with actual Telugu speech** — speak real queries, verify commodity entity extraction is correct
  - "Pamuk ki kimat kab badhegi?" should return Cotton data
  - If wrong commodity → entity extraction is broken (flag to Member A)
- [ ] **Begin demo script draft** — structure:
  - Problem (30s) → Solution (30s) → Live Demo: dashboard + agents (80s) → Voice moment (30s) → Impact (10s)

### Hour 14–18 · Demo Prep + Rehearsal 1

- [ ] **Finalize demo script** — 3 minutes max; keep only what demos cleanly
- [ ] **Verify canned demo path** — test `?demo=canned`, practice mid-demo switch
  - Confirm `/demo/canned/{commodity}` works for Cotton, Paddy, Groundnut
- [ ] **Rehearsal 1 (Hour 18)** — discovery run, no stops, note what drags

### Hour 18–22 · Four Full Rehearsals

- [ ] **Rehearsal 2 (Hour 19)** — rewrite script based on Rehearsal 1 findings
- [ ] **Rehearsal 3 (Hour 20)** — failure mode run: kill backend, disconnect WiFi, trigger Groq 429, practice fallback audio
- [ ] **Rehearsal 4 (Hour 21)** — final timed run, under 3 minutes, record as video; drill Q&A cold immediately after

### Hour 22–24 · Sleep

- [ ] Minimum 2 hours sleep. Shower. Clean clothes.
- Hour 21 rehearsal video is the safety net.

---

## Demo Script (3-Minute Template)

| Time | Beat | Script |
|------|------|--------|
| 0:00 | Problem | "Ramesh grows cotton in Telangana. Last Kharif, he sold ₹200 below MSP. The data was public — in English. Ramesh speaks Telugu." |
| 0:30 | Solution | "KrishiCFO is a Telugu-speaking commodity intelligence advisor — MSP floors, 4 seasons of data, 3-agent AI debate, Telugu voice." |
| 0:50 | Dashboard demo | Select Cotton → charts update → trigger WebSocket debate → narrate agent cards → RecommendationCard updates |
| 1:50 | Voice moment | Speak Telugu query → audio plays back → "Under 7 seconds. In his language. Same 3-agent debate." |
| 2:20 | Close | "4 seasons. 14 commodities. 3 AI agents. All free-tier. We made data speak the farmer's language." |

---

## Q&A Cheat Sheet

| Question | Key Answer |
|----------|-----------|
| Seasonal data — is it actionable? | MSP floor + 4-year context is the most important signal. Real data > fake forecast. |
| Why 3 agents? | Adversarial lenses (Optimist/Pessimist/Risk Analyst) surface conflict score — can't get that from a single prompt. |
| How accurate? | Confidence-labeled (High/Moderate/Low) + conflict score. Honest uncertainty > false precision. |
| Why not ChatGPT? | No our dataset, no multi-agent debate, no Telugu voice. Also: zero rupees. |
| WiFi dies? | Switch to `?demo=canned` — "Let me show you now." |
| Scale to more commodities? | Add CSV, run normalizer — pipeline is commodity-agnostic. |

**Meta-rule:** Every answer ends with a number, a specific technical choice, or "let me show you." Never bluff.

---

## Key Files

| File | Status |
|------|--------|
| `components/VoiceButton.tsx` | New — build Hours 0–6 |
| `fallback/audio_cotton.mp3` | New — generate Hour 0 |
| `fallback/audio_paddy.mp3` | New — generate Hour 0 |
| `fallback/audio_groundnut.mp3` | New — generate Hour 0 |
| `config.py` | Update — lock `voice_id` at Hour 0 |

---

## Critical Risks

| Risk | Mitigation |
|------|-----------|
| ElevenLabs API fails during demo | Pre-generated fallback MP3s ready at Hour 0 |
| Bad Telugu voice quality | Test voice_id at playground before writing any code |
| WhisperFlow unavailable | Groq Whisper Large v3 is drop-in fallback (same interface) |
| Member A's `/voice/query` not ready | CLI-test each stage independently; VoiceButton runs on mock until Hour 6–10 |
| WiFi dies | `?demo=canned` path tested and practiced |
