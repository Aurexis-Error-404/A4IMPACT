# KrishiCFO — PS-14 Implementation Plan
## (Post Adversarial Review — v2.1)

## Context

**Problem:** Indian farmers (e.g. Ramesh, Medak district) lose ₹40K+ per harvest season selling in the wrong mandi at the wrong time — not for lack of data, but because Agmarknet is an English spreadsheet no farmer reads.

**Solution:** KrishiCFO — a Telugu-speaking CFO for Indian farmers. Predicts crop prices via Prophet (Agmarknet data), runs a 4-agent debate (Optimist / Pessimist / Risk → Mediator) adapted from AGENT_IITH's stock market architecture, delivers the recommendation as a voice response in Telugu, shows a line-item ₹ profit breakdown, and sends proactive Twilio SMS alerts before the farmer thinks to ask.

**Key constraints:**
- Agmarknet data NOT downloaded yet → data ingestion is critical path, starts Hour 0
- Bhashini registration takes up to 24h → submit at Hour 0, text output is primary demo path if unavailable
- Free tier only: Groq, Bhashini, Supabase, Railway, Vercel, Upstash, Twilio trial

---

## Critical Fixes from Adversarial Review

| Issue | Original Plan | Fix Applied |
|---|---|---|
| Kurnool is in Andhra Pradesh, not Telangana | Listed as Telangana mandi | **Replaced with Karimnagar** (major turmeric market in Telangana) |
| Groq RPD will be exhausted by 11-call debate | Qwen3-32B for all 4 agents | **Model routing:** agents → Llama 3.1 8B (14,400 RPD); mediator → Qwen3-32B (1 call/query) |
| Voice path <10s with full debate is impossible | Full debate in voice loop | **Voice path decoupled:** single LLM advisory call, not debate |
| 6.8% MAPE claim is unsupported | Claimed 6.8% in pitch | **Removed. Target: 8–12% with tuning, publish actual holdout MAPE per crop** |
| Fake citation source-tier mechanics | Sources like "WhatsApp Group" cited | **Removed source-tier debate citations.** Agents cite actual data values (Prophet bands, price deltas, weather mm) |
| Kelly weights misapplied to sell-timing | Kelly Criterion for portfolio allocation | **Replaced with deterministic rule aggregation** (forecast delta + storage cost + confidence gap) |
| APMC fee ownership wrong | Fee charged to farmer at 1.5% | **Clarified: APMC fee paid by buyer/trader; farmer receives net price after trader deduction** |
| No offline fallback | All APIs required for demo | **Added: canned-data local fallback mode** that runs without any external API calls |
| Farmer cost price never collected | Logic "sell if yhat_lower near cost price" | **Removed** that logic; or make cost price an explicit UI input |
| OpenRouteService in critical path | Live routing API call | **Replaced with hardcoded distance table as primary; ORS as optional enhancement** |

---

## Architecture

### Two Paths — One UI

```
Next.js 14 (Vercel)
  ↕ REST + WebSocket (streaming debate for web path)
FastAPI (Railway)
  │
  ├── VOICE PATH (latency-first, single LLM call)
  │     Groq Whisper STT → Llama 3.1 8B advisory → Bhashini TTS
  │     Target: < 6s text, < 9s audio
  │
  └── WEB PATH (quality-first, full debate)
        Prophet forecast
        → asyncio.gather(Optimist, Pessimist, Risk) via Llama 3.1 8B
        → Debate round (max 1 round) via Llama 3.1 8B
        → Mediator via Qwen3-32B (1 call/query)
        → Telugu wrapper via Llama 3.1 8B
        → WebSocket broadcast
  │
  Supabase (Postgres) + Upstash Redis (forecast cache TTL=1h)
```

**LLM routing (corrected for rate limits):**

| Task | Model | Free RPD | Calls/query |
|---|---|---|---|
| 3 agents (Optimist/Pessimist/Risk) | Llama 3.1 8B Instant | 14,400 | 3 |
| Debate rebuttal | Llama 3.1 8B Instant | 14,400 | ≤3 |
| Mediator synthesis | Qwen3-32B | 1,000 | 1 |
| Telugu response wrapper (voice) | Llama 3.1 8B Instant | 14,400 | 1 |
| Telugu STT | Whisper Large v3 | 2,000 | 1 |
| Query translation (Te→En) | Llama 3.1 8B Instant | 14,400 | 1 |

**Queries per day before Qwen3-32B RPD exhaustion: 1,000 (mediator is the bottleneck)**
**For voice path (no mediator): effectively unlimited via Llama 8B**

**TPM management:** Add 2s stagger between parallel agent calls (`asyncio.sleep(2)`) to spread TPM load across 6s instead of 50ms burst. Aggressive Redis caching means same crop+mandi combo hits cache, not LLM.

---

## Mandis (corrected — all in Telangana)

| Mandi | District | Key Crops |
|---|---|---|
| Warangal | Warangal Urban | Tomato, Chili |
| Hyderabad (Bowenpally) | Medchal | All 4 crops |
| Nizamabad | Nizamabad | Onion, Turmeric |
| **Karimnagar** | Karimnagar | Turmeric, Chili ← replaces Kurnool (AP) |
| Nalgonda | Nalgonda | Tomato, Onion |

---

## Folder Structure

```
krishicfo/
├── backend/                        # Python FastAPI → Railway
│   ├── main.py                     # app, CORS, WebSocket, lifespan
│   ├── config.py                   # Pydantic Settings
│   ├── requirements.txt
│   ├── agents/
│   │   ├── llm.py                  # Groq client, extract_last_json, exponential backoff on 429
│   │   ├── optimist.py             # Llama 8B: Prophet upper band + seasonality signals
│   │   ├── pessimist.py            # Llama 8B: Prophet lower band + glut/weather signals
│   │   ├── risk.py                 # Llama 8B: transport/APMC/weather disruptions
│   │   ├── debate.py               # 1-round max rebuttal; deterministic rule aggregation
│   │   ├── mediator.py             # Qwen3-32B: 3 farmer personas + conflict scoring
│   │   └── advisory.py             # Llama 8B: single-call advisory for voice path
│   ├── data/
│   │   ├── agmarknet_ingest.py     # CSV parse, outlier flagging (NOT removal), Supabase upsert
│   │   ├── agmarknet_scraper.py    # Selenium fallback if site is down
│   │   ├── weather.py              # Open-Meteo rainfall (no key)
│   │   └── transport.py            # hardcoded distance table (primary) + ORS (optional)
│   ├── forecasting/
│   │   ├── prophet_model.py        # fit/predict, rolling-origin MAPE, holiday regressors
│   │   └── model_cache.py          # Upstash Redis TTL=1h + in-memory dict fallback
│   ├── profit/
│   │   └── calculator.py           # line-item ₹ breakdown (transport, APMC buyer-side, labor, packaging)
│   ├── voice/
│   │   ├── stt.py                  # Groq Whisper, language="te"
│   │   └── tts.py                  # Bhashini TTS (5s timeout) → AI4Bharat Indic-TTS fallback
│   ├── alerts/
│   │   └── sms.py                  # Twilio Unicode Telugu SMS (verified numbers only)
│   ├── fallback/
│   │   └── canned_demo.py          # static pre-computed responses for offline/contingency demo
│   ├── db/
│   │   ├── supabase_client.py      # async Supabase wrapper
│   │   └── schema.sql
│   └── routers/
│       ├── analyze.py              # POST /analyze, WS /ws
│       ├── voice.py                # POST /voice/query, /voice/transcribe
│       ├── forecast.py             # GET /forecast/{crop}/{mandi}
│       ├── profit.py               # POST /profit/calculate
│       ├── alerts.py               # POST /alerts/sms/subscribe, /send
│       └── fpo.py                  # GET /fpo/choropleth/{crop}
│
└── frontend/                       # Next.js 14 → Vercel
    ├── app/
    │   ├── page.tsx                # Landing
    │   ├── dashboard/page.tsx      # Farmer interface (text-first; voice = enhancement)
    │   └── fpo/page.tsx            # FPO choropleth dashboard
    ├── components/
    │   ├── VoiceButton.tsx         # MediaRecorder → blob → API → audio playback (optional)
    │   ├── AgentDebate.tsx         # 4 agent cards (adapted from AGENT_IITH DebateSection.jsx)
    │   ├── PriceChart.tsx          # Prophet yhat + confidence bands (Recharts)
    │   ├── ProfitBreakdown.tsx     # Kirana receipt-style ₹ table
    │   ├── MandiSelector.tsx       # 5 Telangana mandis (updated)
    │   ├── CropSelector.tsx        # Tomato / Onion / Chili / Turmeric
    │   └── ChoroplethMap.tsx       # react-simple-maps + telangana.geojson
    ├── lib/
    │   ├── api.ts                  # typed fetch wrappers with canned-data fallback
    │   └── websocket.ts            # WS hook + REST polling fallback (exponential backoff)
    └── public/
        └── telangana.geojson       # district boundary GeoJSON
```

---

## Supabase Schema (`backend/db/schema.sql`)

```sql
CREATE TABLE price_records (
  id            BIGSERIAL PRIMARY KEY,
  state         TEXT DEFAULT 'Telangana',
  district      TEXT NOT NULL,
  mandi         TEXT NOT NULL,
  commodity     TEXT NOT NULL,
  variety       TEXT,
  arrival_date  DATE NOT NULL,
  modal_price   NUMERIC(10,2) NOT NULL,
  min_price     NUMERIC(10,2),
  max_price     NUMERIC(10,2),
  is_anomaly    BOOLEAN DEFAULT FALSE,  -- flagged, NOT removed
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX ON price_records(mandi, commodity, variety, arrival_date);
CREATE INDEX ON price_records(commodity, mandi, arrival_date DESC);

CREATE TABLE forecasts (
  id            BIGSERIAL PRIMARY KEY,
  crop          TEXT NOT NULL,
  mandi         TEXT NOT NULL,
  forecast_date DATE NOT NULL,
  yhat          NUMERIC(10,2),
  yhat_lower    NUMERIC(10,2),
  yhat_upper    NUMERIC(10,2),
  mape_rolling  NUMERIC(6,4),  -- rolling-origin MAPE across 3 windows, not single holdout
  model_run_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON forecasts(crop, mandi, forecast_date);

CREATE TABLE crop_signals (
  id            BIGSERIAL PRIMARY KEY,
  run_id        UUID NOT NULL,
  crop          TEXT NOT NULL,
  mandi         TEXT NOT NULL,
  agent         TEXT NOT NULL,  -- optimist|pessimist|risk|mediator
  verdict       TEXT,
  confidence    INTEGER,
  reasons       JSONB,          -- [{text, data_value, weight}] — no fake source citations
  decision      TEXT,
  conflict_score TEXT,
  trigger_advice TEXT,
  rationale     TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON crop_signals(run_id);

CREATE TABLE farmer_sessions (
  id            BIGSERIAL PRIMARY KEY,
  phone_hash    TEXT,           -- SHA-256 of phone, never store raw
  crop          TEXT,
  mandi         TEXT,
  role          TEXT CHECK (role IN ('user','assistant')),
  content_te    TEXT,
  content_en    TEXT,
  -- No audio_url stored: privacy
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE profit_calculations (
  id              BIGSERIAL PRIMARY KEY,
  run_id          UUID NOT NULL,
  crop            TEXT,
  mandi           TEXT,
  quantity_qtl    NUMERIC(8,2),
  net_profit      NUMERIC(12,2),
  incremental_gain NUMERIC(12,2),
  line_items      JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sms_alerts (
  id            BIGSERIAL PRIMARY KEY,
  phone_hash    TEXT NOT NULL,  -- SHA-256, not raw phone
  twilio_to     TEXT NOT NULL,  -- raw phone stored only here for Twilio, delete after send
  crop          TEXT NOT NULL,
  mandi         TEXT NOT NULL,
  threshold_pct NUMERIC(5,2) DEFAULT 15.0,
  message_te    TEXT,
  twilio_sid    TEXT,
  sent_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE fpo_district_stats (
  id              BIGSERIAL PRIMARY KEY,
  district        TEXT NOT NULL,
  crop            TEXT NOT NULL,
  avg_modal_price NUMERIC(10,2),
  price_trend_pct NUMERIC(6,2),
  computed_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX ON fpo_district_stats(district, crop, computed_at::DATE);
```

---

## API Route Map

```
GET  /health                              → {status, models_loaded, prophet_crops, cache_hits}
WS   /ws                                 → streams: agent results, debate turns, mediator

POST /analyze                            → {crop, mandi, quantity_qtl, persona, phone?}
GET  /forecast/{crop}/{mandi}            → {forecast_14d, current_price, mape_rolling}
POST /profit/calculate                   → {run_id, quantity_qtl, farm_km_to_mandi, cost_price_per_qtl?}
POST /voice/transcribe                   → multipart audio → {text_en, text_te}
POST /voice/query                        → {audio_base64, crop, mandi, persona}
                                            → single LLM advisory call (NOT full debate)
POST /alerts/sms/subscribe               → {phone, crop, mandi, threshold_pct}
POST /alerts/sms/send                    → trigger (internal/cron)
GET  /fpo/choropleth/{crop}              → GeoJSON FeatureCollection with price data
POST /admin/ingest                       → trigger Agmarknet CSV ingest (token-gated)
POST /admin/refit-prophet                → refit all models (token-gated)
GET  /demo/canned/{crop}/{mandi}         → pre-computed offline demo response
```

---

## Agent System Prompts (post adversarial review)

**No fake source citations.** Agents cite actual computed data values:
- Prophet `yhat`, `yhat_upper`, `yhat_lower` (injected as numbers)
- Price delta over last 7 days (computed from Agmarknet)
- Rainfall mm forecast from Open-Meteo (injected as number)
- Arrival volume trend (computed from Agmarknet)

**Debate simplification — removed:**
- Source-tier Bayesian scoring (was hallucinated citations)
- Kelly Criterion weights (misapplied from stock domain)
- Delphi multi-round updates (replaced with single rebuttal round)

**Replaced with deterministic rule aggregation in `debate.py`:**
```python
def aggregate_verdicts(optimist, pessimist, risk):
    # Count weighted verdicts
    sell_score = 0
    hold_score = 0
    for agent_result, weight in [(optimist, 1.0), (pessimist, 1.2), (risk, 1.5)]:
        if "SELL" in agent_result["verdict"]:
            sell_score += weight * (agent_result["confidence"] / 100)
        else:
            hold_score += weight * (agent_result["confidence"] / 100)
    conflict = "HIGH" if abs(sell_score - hold_score) < 0.3 else \
               "MEDIUM" if abs(sell_score - hold_score) < 0.6 else "LOW"
    return {"sell_score": sell_score, "hold_score": hold_score, "conflict": conflict}
```

**Mediator personas** (3 farmer types, Qwen3-32B only):
- `small_farmer` → conservative (risk weight 1.5×): SELL_NOW if risk agent says HOLD
- `medium_farmer` → balanced: factor ₹50/quintal/week storage cost vs. price gain
- `fpo` → moderate (bulk transport ₹12/km, can split across 2 mandis)

**Note on SELL_NOW logic:** Removed "sell if yhat_lower near cost price" (requires cost price input never collected). Replaced with: "sell if yhat_lower < current_modal_price × 0.9" — observable from data alone.

---

## Voice Pipeline (decoupled from debate)

```
Browser MediaRecorder → WAV blob
→ POST /voice/query
→ Groq Whisper Large v3 (language="te") → text_te           [0.7s]
→ Llama 3.1 8B: translate text_te → English intent          [0.4s]
→ Fetch Prophet cache for crop+mandi (Redis, usually hit)    [0.1s]
→ Llama 3.1 8B: single advisory call                        [1.2s]
  (receives: forecast summary + profit calc output + persona)
→ Bhashini TTS (5s timeout)                                  [0.8s]
  → fallback: AI4Bharat Indic-TTS
→ Return {text_response_te, audio_base64_te, run_id}
→ Frontend: show text immediately, play audio when ready

Text response target: < 3s. Audio target: < 7s.
```

**Voice path does NOT trigger the 4-agent debate.** Debate runs only on web path. This removes the Qwen3-32B RPD cost from every voice query.

**Bhashini contingency:** If Bhashini is not approved by demo time, show text response in Telugu and skip audio. Pre-generate 3 sample audio clips (Tomato/Warangal, Onion/Hyderabad, Chili/Karimnagar) for the demo's voice moment.

---

## Profit Calculator Formula (`backend/profit/calculator.py`)

```
TATA_ACE_RATE     = ₹17/km  (Telangana, loaded with produce)
APMC_BUYER_FEE    = 1.5%    — PAID BY BUYER/TRADER, reduces the price farmer receives
                              Represented as: effective_farmer_price = modal_price × (1 - 0.015)
LABOR             = ₹200/quintal (loading + unloading, farmer-borne)
PACKAGING         = ₹15/quintal (gunny bags)
COLD_STORAGE      = ₹50/quintal/week (medium farmer only)
FPO_TRANSPORT     = ₹12/km   (bulk discount, FPO persona)

trucks            = ceil(quantity_qtl / 10)
transport_cost    = trucks × km × rate_per_km
effective_price   = target_price × (1 - 0.015)      # net of APMC buyer deduction
gross_revenue     = quantity_qtl × effective_price
net_profit        = gross_revenue - transport_cost - labor - packaging - storage_cost

incremental_gain  = net_profit(target_date) - net_profit(sell_today)

# Cost price input (optional — show input field in UI)
# If provided: show break-even analysis
# If not provided: omit break-even line from output
```

---

## Agmarknet Data Ingestion (`backend/data/agmarknet_ingest.py`)

**Target:** Tomato, Onion, Chili (Dry Chilli), Turmeric × 5 Telangana mandis (Warangal, Bowenpally, Nizamabad, Karimnagar, Nalgonda), 2022–present.

**Commodity normalization:**
```python
{"Tomato": "Tomato", "Onion": "Onion", "Dry Chilli": "Chili",
 "Chilli": "Chili", "Turmeric": "Turmeric"}
```

**Anomaly handling (changed from adversarial review — DO NOT remove outliers):**
```python
# IQR is used to FLAG anomalies, not remove them
# Prophet handles supply shocks better when they are present (as changepoints)
# Setting is_anomaly=True lets the UI show "unusual price event" tooltip
Q1 = group["modal_price"].quantile(0.25)
Q3 = group["modal_price"].quantile(0.75)
IQR = Q3 - Q1
df["is_anomaly"] = (df["modal_price"] < Q1 - 2.5*IQR) | (df["modal_price"] > Q3 + 2.5*IQR)
```

**Gap filling:** Forward-fill up to 3 consecutive missing days. Drop rows with > 3-day gaps (non-functional market periods).

**Fallback sources if agmarknet.gov.in is down:**
1. `data.gov.in` — "Telangana commodity daily" CSVs
2. `github.com/akhilesh-k/agmarket-price-data` — 3 years of historical data

---

## Prophet Model Setup (`backend/forecasting/prophet_model.py`)

```python
Prophet(
    changepoint_prior_scale=0.05,  # conservative — agri prices have seasonal structure
    seasonality_prior_scale=10.0,
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    interval_width=0.80,
)
```

- Add `country_holidays(country_name="IN")` — Diwali, Sankranti demand effects
- External regressor: `rainfall_mm` from Open-Meteo for **Tomato only** initially (validate before adding others)
- **MAPE reporting (corrected):** Rolling-origin backtest over 3 windows (last 90 / last 60 / last 30 days). Publish actual MAPE per crop-mandi pair. Do NOT claim a specific number in the pitch — say "X% average across our 4 crops, details in dashboard."
- **Do NOT run ablations during the hackathon** — default to no rainfall regressor unless Tomato+Warangal shows measurable improvement in first fit.

---

## Offline / Contingency Demo Mode (`backend/fallback/canned_demo.py`)

Pre-compute and store 3 full demo responses as JSON at build time:

```python
CANNED_DEMOS = {
    ("Tomato", "Warangal"): {
        "forecast_14d": [...],  # real computed values from last successful run
        "agents": {"optimist": {...}, "pessimist": {...}, "risk": {...}},
        "mediator": {"decision": "SELL_NEXT_WEEK", "confidence": 74, ...},
        "profit": {"net_profit": 48000, "incremental_gain": 9200, "line_items": [...]},
        "voice_te": "నవంబర్ 22న వరంగల్‌లో 40 క్వింటాళ్లు అమ్మండి...",
        "audio_file": "public/canned/tomato_warangal.mp3",  # pre-generated
    },
    # ... Onion/Hyderabad, Chili/Karimnagar
}
```

Frontend has a `?demo=canned` query param that switches all API calls to `/demo/canned/{crop}/{mandi}`. Activate this if Railway goes cold or WiFi dies.

---

## Critical AGENT_IITH Files to Port to Python

| AGENT_IITH File | Port to | What to preserve |
|---|---|---|
| `backend/agents/llm.js` | `agents/llm.py` | `extractLastJson` bracket-depth parser, exponential backoff on 429 |
| `backend/agents/debate.js` | `agents/debate.py` | Only the parallel execution pattern and early convergence check; **remove** source tiers, Kelly, Delphi |
| `backend/agents/mediator.js` | `agents/mediator.py` | Conflict scoring (HIGH/MEDIUM/LOW) and persona differentiation; replace Kelly with `aggregate_verdicts()` |
| `backend/server.js` → `runPipeline()` | `routers/analyze.py` | Sequencing: parallel agents → debate → mediator → WebSocket broadcast |
| `market-intelligence-frontend/src/components/DebateSection.jsx` | `AgentDebate.tsx` | WS state machine, expanding reasoning chains, confidence bars |

**Python asyncio translation:**
```python
# 2s stagger (not 50ms) to spread TPM load across 6s window
results = await asyncio.gather(
    run_optimist(context),
    run_pessimist(context, delay=2),
    run_risk(context, delay=4),
    return_exceptions=True
)
```

---

## 48-Hour Execution Order

### Hour 0–2: Setup Sprint (all 3 parallel)

**Member A (Backend):**
- Submit Bhashini registration (bhashini.gov.in/ulca/model) — async, continue without
- Create Railway project, set env vars
- Run `schema.sql` in Supabase SQL editor
- Init FastAPI project, `requirements.txt`, deploy ASAP to Railway (verify Prophet installs cleanly — this is a known packaging risk, do it first)

**Member B (Data):**
- **CRITICAL PATH:** Download Agmarknet CSVs — Tomato + Onion + Chili + Turmeric in Telangana, 2022–present
  - Primary: agmarknet.gov.in/SearchCommodity.aspx
  - Fallback 1: data.gov.in
  - Fallback 2: github.com/akhilesh-k/agmarket-price-data
- Run `agmarknet_ingest.py` immediately

**Member C (Frontend):**
- Create Next.js 14 on Vercel, configure `NEXT_PUBLIC_API_URL`
- Scaffold `AgentDebate.tsx` (copy DebateSection.jsx from AGENT_IITH)
- Wire `VoiceButton.tsx` with MediaRecorder — no backend needed yet
- Pre-generate 3 canned Telugu audio clips (TTS.ai or Google TTS if Bhashini not approved yet) — **insurance for demo day**

### Milestone: Hour 4 — Smoke Tests

- Railway deploys successfully with Prophet (no packaging failure)
- Supabase has 5,000+ rows in `price_records`
- `GET /forecast/Tomato/Warangal` returns a 14-day forecast

If any of these 3 fails, stop and fix before proceeding.

### Hour 4–12: Text-First Demo Path (scope freeze target)

**A:** `llm.py`, `optimist.py`, `pessimist.py`, `risk.py` (Llama 8B), `advisory.py` (single-call voice advisory)
**B:** First Prophet fit (Tomato/Warangal). `profit/calculator.py`. `ProfitBreakdown.tsx`.
**C:** `PriceChart.tsx` + `AgentDebate.tsx` consuming real API. `MandiSelector.tsx` with Karimnagar.

**Milestone Hour 12 — TEXT-ONLY DEMO WORKS:**
- `POST /analyze` returns 4 agent results via REST (not WS yet)
- Frontend shows agent cards + profit breakdown with real data
- FREEZE SCOPE HERE if behind schedule. Do not add features until this is solid.

### Hour 12–20: Real-Time + Voice

**A:** `debate.py` (deterministic aggregation), `mediator.py` (Qwen3-32B), WebSocket broadcast
**B:** Connect `AgentDebate.tsx` to WebSocket. Animate agent cards appearing sequentially.
**C:** Voice pipeline on CLI: Whisper → Llama 8B advisory → Bhashini/AI4Bharat TTS

Milestone Hour 20: Voice loop closes end-to-end, even if ugly.

### Hour 20–24: Integration

Members A + B pair for 3 hours — real API meets real frontend.
C: wire `VoiceButton.tsx` → `/voice/query` → `<audio>` playback.

**Hour 24 DRY RUN:** Full demo path, text + voice. Will have bugs. Fix the critical ones only.

### Hour 24–32: Second-tier + Polish

**A:** `weather.py`, refit Tomato Prophet with rainfall; `alerts/sms.py` (verify Twilio to pre-registered number)
**B:** FPO dashboard (`ChoroplethMap.tsx`); visual polish — chart draw-in, receipt animation
**C:** Twilio cron; seed "3 days ago" alert; build `canned_demo.py` with real computed values

### Hour 32–40: Bug bash + Rehearsal

All three walk every demo path. Member C: first timed 3-min rehearsal.
**A:** Redis caching + graceful degradation (Prophet fails → 7-day rolling average)
**B:** Micro-interactions, mobile-first polish

### Hour 40–46: Pitch mastery

6+ full rehearsals. Record backup video. Q&A cards drilled cold.
Pre-coordinate judge's phone for Twilio SMS moment (Twilio trial requires pre-verified numbers).
Activate `?demo=canned` and verify it works without any network calls.

### Hour 46–48: Sleep.

---

## Feature Cut Priority

| Priority | Feature | Cut threshold |
|---|---|---|
| P0 Never cut | Prophet forecast + confidence bands | — |
| P0 Never cut | 4-agent debate + mediator (text output) | — |
| P0 Never cut | Agmarknet data displayed | — |
| P0 Never cut | Profit calculator (line items) | — |
| P1 Cut if fails | Telugu voice (STT + TTS) | If audio broken → show text in Telugu only |
| P1 Cut if fails | WebSocket streaming | If Railway WS blocks → REST polling (already in `websocket.ts`) |
| P1 Cut if fails | Twilio SMS | If Twilio trial limits or unverified number → screenshot fallback |
| P2 Cut at Hour 30 | FPO choropleth | If behind schedule |
| P3 Drop freely | Open-Meteo rainfall regressor | Default: no regressor |
| P3 Drop freely | OpenRouteService | Hardcoded distance table is primary |
| P4 Drop freely | Upstash Redis | In-memory dict fallback already in `model_cache.py` |

**Hardcoded distance table (primary for profit calc):**
```python
MANDI_DISTANCES_KM = {
    ("Warangal", "Warangal"): 5,    ("Warangal", "Hyderabad"): 150,
    ("Nalgonda", "Hyderabad"): 80,  ("Nalgonda", "Warangal"): 90,
    ("Nizamabad", "Nizamabad"): 5,  ("Nizamabad", "Hyderabad"): 175,
    ("Karimnagar", "Karimnagar"): 5, ("Karimnagar", "Hyderabad"): 165,
    ("Karimnagar", "Warangal"): 70, ("Hyderabad", "Hyderabad"): 5,
}
```

---

## Verification Checklist

Run in order before demo. Do NOT skip.

```sql
-- Step 1: Data integrity
SELECT commodity, mandi, COUNT(*), MIN(arrival_date), MAX(arrival_date),
       SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalies
FROM price_records GROUP BY commodity, mandi ORDER BY commodity, mandi;
-- Expect: 20 rows (4 crops × 5 mandis), each 300+ records
-- Karimnagar should appear (not Kurnool)
```

```bash
# Step 2: Prophet + MAPE
curl http://localhost:8000/forecast/Tomato/Warangal
# Expect: HTTP 200, 14-day forecast, mape_rolling present (accept any value — do not claim specific %)

# Step 3: Text-path debate (no WS needed)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"crop":"Tomato","mandi":"Warangal","quantity_qtl":50,"persona":"medium_farmer"}'
# Expect: run_id. Then via WS within 15s: optimist, pessimist, risk, mediator events

# Step 4: Voice round-trip
curl -X POST http://localhost:8000/voice/query \
  -F "audio=@test_telugu.wav" -F "crop=Tomato" -F "mandi=Warangal" -F "persona=small_farmer"
# Expect within 7s: text_response_te (Telugu text), audio_base64_te
# Play audio. If Bhashini unavailable: text_response_te must still be present

# Step 5: Profit
curl -X POST http://localhost:8000/profit/calculate \
  -d '{"run_id":"<from step 3>","quantity_qtl":50,"farm_km_to_mandi":45}'
# Expect: 5+ line items, incremental_gain present

# Step 6: Canned demo
curl http://localhost:8000/demo/canned/Tomato/Warangal
# Expect: full pre-computed response, no external API calls triggered

# Step 7: SMS (pre-verified number only)
curl -X POST http://localhost:8000/alerts/sms/send
# Verify in Twilio console dashboard

# Step 8: WS resilience
# Kill Railway → frontend shows "Reconnecting..." → switches to REST polling → data still shows
```

---

## Requirements (`backend/requirements.txt`)

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
websockets==12.0
python-multipart==0.0.9
httpx==0.27.0
pydantic-settings==2.0.0
supabase==2.5.0
redis==5.0.4
prophet==1.1.5
pandas==2.2.2
scikit-learn==1.4.0
groq==0.9.0
twilio==9.2.0
python-dotenv==1.0.0
numpy==1.26.4
```

**Hour 4 packaging test (Railway):** Deploy a minimal `main.py` that imports `from prophet import Prophet` and returns `GET /health → 200`. If this fails, switch to `neuralprophet` or `statsmodels.tsa.holtwinters.ExponentialSmoothing` as Prophet fallback.
