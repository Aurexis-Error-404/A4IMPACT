# Backend Implementation Plan

**Owner**: Member A (Backend)
**Branch**: `backend-implementation`
**Scope**: REST API + AI recommendation pipeline + WebSocket debate stream. Voice deferred to Phase 6.
**Spec source**: `.claude/project.md` (v3.0) + `docs/member_a_backend (1).html`

---

## Phase 0 — Scaffolding (~30 min)

Goal: project structure exists, dev server boots, `/health` responds.

### Create directory structure

```
backend/
  __init__.py
  main.py
  config.py
  requirements.txt
  .env.example
  .gitignore
  data/
    __init__.py
    loader.py
    models.py
  agents/
    __init__.py
    llm.py
    season_optimist.py
    season_pessimist.py
    risk_analyst.py
    mediator.py
  routers/
    __init__.py
    health.py
    commodities.py
    series.py
    insights.py
    recommendation.py
    alerts.py
    ws.py
    demo.py
  services/
    __init__.py
    insight_calculator.py
    recommendation_cache.py
  fallback/
    __init__.py
    canned_responses.py
```

### `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
httpx==0.27.0
pydantic-settings==2.0.0
python-dotenv==1.0.0
groq==0.9.0
websockets==12.0
```

### `config.py`

Pydantic Settings with: `GROQ_API_KEY`, `ALLOWED_ORIGIN` (default `http://localhost:3000`), `DATA_PATH` (default `../crop_data/season_report_summary.json`).

### `main.py`

- `@asynccontextmanager` lifespan that loads the JSON into `app.state.store`
- `CORSMiddleware` registered **before** routers
- Global exception handlers: `NotFoundError`, `ValidationError`, generic `Exception`
- Mount all routers

### `.env.example`

```
GROQ_API_KEY=
ALLOWED_ORIGIN=http://localhost:3000
DATA_PATH=../crop_data/season_report_summary.json
```

### Gate

```bash
uvicorn main:app --reload --port 8000
curl http://localhost:8000/health
# → {"status":"ok","commodities":14,"records":49}
```

---

## Phase 1 — Data layer + basic REST (~1.5 hours)

Goal: frontend can fetch groups, commodities, series, and computed insights.

### `data/loader.py`

- `Store` dataclass: `records[]`, `groups[]`, `commodities_by_group{group: [commodity]}`, `series_by_key{(group, commodity): [record]}` (pre-sorted ascending by `season_year`)
- `load(path) -> Store` — reads JSON once, builds indexes

### `data/models.py`

Pydantic response models matching frontend TypeScript contracts in `CLAUDE.md` §Data contract:

- `SeasonRecord` — mirrors JSON record
- `SeriesRecord` — per-season shape for `/api/commodity-series`
- `CommodityInsightSummary` — full insight shape (17 fields, see CLAUDE.md for types)
- `AlertItem`, `CommodityCardSummary`

### `services/insight_calculator.py`

Pure functions (no LLM), no side effects:

| Function | Signature | Logic |
|---|---|---|
| `latest_reference_price` | `(records) -> float \| None` | Prefer Kharif, fallback Rabi, on latest season |
| `latest_delta_pct` | `(records) -> float` | `(price - msp) / msp`, **decimal** |
| `price_trend` | `(records) -> Literal["up","down","flat"]` | Last two seasons' reference prices |
| `trend_change_pct` | `(records) -> float` | Magnitude of last-season delta |
| `highest_season` | `(records) -> str` | Season with highest reference price |
| `lowest_season` | `(records) -> str` | Season with lowest reference price |
| `season_availability` | `(records) -> Literal[...]` | Presence of Kharif vs Rabi across all seasons |
| `kharif_rabi_shares` | `(records) -> tuple[float, float]` | Decimal shares of total arrivals |

### Routers

| Route | File | Response |
|---|---|---|
| `GET /api/commodity-groups` | `routers/commodities.py` | `["Cereals","Fibre Crops","Oil Seeds","Pulses"]` |
| `GET /api/commodities?group={g}` | `routers/commodities.py` | `["Cotton","Groundnut",...]` |
| `GET /api/commodity-series?group={g}&commodity={c}` | `routers/series.py` | 4 season records |
| `GET /api/commodity-insights?group={g}&commodity={c}` | `routers/insights.py` | Deterministic insight summary (no LLM) |

### Gate

All 4 GET endpoints return HTTP 200 with valid JSON matching frontend types. Unknown group/commodity → 404 with suggestion.

---

## Phase 2 — AI recommendation pipeline (~3 hours)

Goal: `POST /api/recommendation/{commodity}` returns full `CommodityInsightSummary` powered by 3 parallel LLM agents + mediator.

### `agents/llm.py`

- `async def call_llm(messages, model="llama-3.1-8b-instant", max_retries=3) -> str`
- Exponential backoff on HTTP 429: 2s → 4s → 8s
- `extract_last_json(text) -> dict` — bracket-depth parser, handles LLM's chattiness before/after the JSON block

### Three analyst agents

Each module exports:
- `SYSTEM_PROMPT: str`
- `async def analyze(commodity, series_records, insight_summary) -> dict`

**`season_optimist.py`** — hunts for price-above-MSP seasons, uptrend signals, strong Kharif/Rabi pairs. Output:
```json
{"verdict":"HOLD|LEAN_SELL|DEFER|PROTECT","confidence":0-100,"reasoning":"...","key_seasons":["2024-25"]}
```

**`season_pessimist.py`** — hunts for below-MSP events, declining arrivals, glut signals. Same output shape.

**`risk_analyst.py`** — computes MSP floor proximity, Kharif/Rabi coverage risk, sparse-data risk. Output adds `risk_level: "Low"|"Watch"|"High"`.

### `agents/mediator.py`

Single Llama 8B call synthesizing all 3 verdicts + insight summary. Output mapped exactly to TypeScript union types:

```json
{
  "recommendationLabel": "Hold|Lean sell|Defer|Protect",
  "confidenceLabel": "High confidence|Moderate confidence|Low confidence",
  "riskLevel": "Low|Watch|High",
  "recommendationRationale": "2-3 sentence farmer-readable rationale",
  "conflict_score": "LOW|MEDIUM|HIGH"
}
```

**System prompt includes** the exact allowed string list — mediator is warned that any deviation breaks the frontend.

### `services/recommendation_cache.py`

- In-memory dict: `{commodity: (result, expires_at)}`
- 1-hour TTL
- `get(commodity) -> dict | None`, `set(commodity, result) -> None`

### `routers/recommendation.py`

`POST /api/recommendation/{commodity}`:
1. Check cache → return if hit
2. Fetch series + insight summary (deterministic) from Phase 1 services
3. `asyncio.gather()` of 3 agents with 2s stagger (`asyncio.sleep(2)` inside wrapped tasks)
4. Feed results + insight to mediator
5. Merge mediator output into deterministic `CommodityInsightSummary`
6. Cache + return

### Deterministic fallback in `agents/mediator.py`

`def aggregate_verdicts(optimist, pessimist, risk) -> dict` — pure rule-based scoring. Called when any LLM agent fails or returns unparseable JSON. Recommendation ALWAYS returns a valid response.

### Gate

```bash
curl -X POST http://localhost:8000/api/recommendation/Cotton
# Returns within 8s, valid CommodityInsightSummary, all string literals correct
```

---

## Phase 3 — WebSocket debate stream (~1.5 hours)

Goal: frontend `RecommendationCard` shows agents arriving sequentially with ~2s between each.

### `routers/ws.py`

`WS /ws`:
- Client sends `{"action":"start","commodity":"Cotton"}`
- Server runs agents sequentially (not gathered) with 2s stagger
- Streams 4 events: `optimist`, `pessimist`, `risk`, `mediator`
- Event envelope:
  ```json
  {"stage":"optimist","data":{...agent output...},"ts":"2026-04-17T12:34:56Z"}
  ```
- Reuses agent modules from Phase 2 — no prompt duplication

### Gate

- Frontend WS connection succeeds
- 4 events arrive in ~12s total
- Final event has full mediator output
- Connection closes cleanly after mediator event

---

## Phase 4 — Alerts + canned fallback (~1 hour)

Goal: risk panel has data; offline demo works.

### `routers/alerts.py`

`GET /api/alerts` → list of `AlertItem` for commodities flagged `Watch` or `High` risk.
- Computed from `insight_calculator` + one cached mini-LLM call per commodity for the headline text
- Response cached 1h

### `fallback/canned_responses.py`

Pre-computed full responses for 3 commodities: **Cotton, Paddy (Common), Groundnut**. Static dict. Zero external calls.

### `routers/demo.py`

`GET /demo/canned/{commodity}` → serves canned JSON.

### Gate

- `GET /api/alerts` returns list with valid severity fields
- `GET /demo/canned/Cotton` works with WiFi disabled

---

## Phase 5 — Hardening + integration test (~1 hour)

Goal: no surprises during frontend integration.

- Exception handlers return frontend-friendly error shapes for 404 / 400 / 429 / 500
- CORS confirmed working against `localhost:3000` (test with browser DevTools)
- Run 10 rapid `POST /api/recommendation/` calls — cache absorbs most; verify no 500s
- Full smoke-test curl script in `backend/scripts/smoke.sh` (optional but recommended)

### Gate

All curl commands in `CLAUDE.md §Smoke tests` return 200 with valid shapes. Frontend loads `/` and `/commodity/[slug]` without console errors when pointed at `localhost:8000`.

---

## Phase 6 (DEFERRED) — Voice pipeline

Not in this plan. Added only after Phases 0-5 are solid.

Scope when resumed:
- WhisperFlow STT or OpenAI Whisper API
- ElevenLabs Multilingual v2 TTS (5s timeout, text-only fallback)
- `POST /voice/query` — STT → entity extraction → 3 agents → synthesis → TTS
- `POST /voice/transcribe` — STT only
- Voice-specific `voice_advisory.py` (single-call advisory, NOT full debate)

---

## Verification (end-to-end)

After Phase 5:

1. **Data**: `curl http://localhost:8000/health` → `{"status":"ok","commodities":14,"records":49}`
2. **Deterministic REST**: all GET endpoints return valid shapes
3. **AI recommendation**: `POST /api/recommendation/Cotton` → valid `CommodityInsightSummary` in <8s
4. **WebSocket debate**: JS test script opens `/ws`, receives 4 staged events in ~12s
5. **Alerts**: `GET /api/alerts` returns at least 1 commodity flagged
6. **Canned fallback**: `GET /demo/canned/Cotton` works with network disabled
7. **CORS**: frontend at `localhost:3000` fetches all endpoints without browser errors
8. **Rate-limit resilience**: 10 rapid recommendation calls don't produce 500s

## Critical files (order of creation)

1. `backend/requirements.txt`
2. `backend/config.py`
3. `backend/.env.example`
4. `backend/data/loader.py`, `backend/data/models.py`
5. `backend/main.py` (imports loader + config)
6. `backend/routers/health.py` (verify server boots)
7. `backend/services/insight_calculator.py`
8. `backend/routers/commodities.py`, `series.py`, `insights.py`
9. `backend/agents/llm.py`
10. `backend/agents/{season_optimist,season_pessimist,risk_analyst,mediator}.py`
11. `backend/services/recommendation_cache.py`
12. `backend/routers/recommendation.py`
13. `backend/routers/ws.py`
14. `backend/routers/alerts.py`
15. `backend/fallback/canned_responses.py`, `backend/routers/demo.py`
