# CLAUDE.md — KrishiCFO Backend

Context file for Claude Code sessions. Read `.claude/project.md` for full product spec and `plan.md` for phase-by-phase implementation roadmap.

---

## Project snapshot

KrishiCFO is a **season-wise commodity intelligence dashboard**. Backend is a FastAPI service that loads a normalized JSON dataset into memory at startup and serves REST + WebSocket endpoints to a Next.js frontend. **No database.** No Prophet. No mandi or daily data. 14 commodities across 4 groups, 4 seasons (2022-23 → 2025-26).

## My role

**Member A — Backend Engineer.** I own `backend/`. I do not touch `frontend/` or the raw CSVs in `crop_data/`. I read `crop_data/season_report_summary.json` — nothing else from that folder.

## Tech stack (pinned)

- Python 3.11+, FastAPI 0.115, uvicorn 0.30, httpx 0.27
- `pydantic-settings` 2.0 for config, `python-dotenv` 1.0
- Groq API (`llama-3.1-8b-instant`) for all LLM agents via the official `groq==0.9.0` SDK
- `asyncio` for parallel agent execution
- `websockets==12.0` for the debate stream
- **Not used**: database, Redis, Supabase, Prophet, scikit-learn, pandas

## Data contract (silent-failure territory)

Frontend TypeScript is **strict mode**. These string literals and number types MUST match exactly — any drift breaks the UI without a runtime error.

| Field | Allowed values |
|---|---|
| `priceTrend` | `"up"` \| `"down"` \| `"flat"` (lowercase) |
| `riskLevel` | `"Low"` \| `"Watch"` \| `"High"` |
| `recommendationLabel` | `"Hold"` \| `"Lean sell"` \| `"Defer"` \| `"Protect"` |
| `confidenceLabel` | `"High confidence"` \| `"Moderate confidence"` \| `"Low confidence"` |
| `seasonAvailability` | `"Kharif only"` \| `"Rabi only"` \| `"Both"` \| `"Sparse"` |
| `latestDeltaPct` | **decimal** (0.12 means 12%), not whole percent |
| `kharifShare`, `rabiShare` | decimal (sum ≤ 1.0) |

Ground truth for contracts: `frontend/lib/canned-data.ts` on `origin/front_data` branch. When in doubt, read that file before inventing a shape.

## Data source

- **File**: `crop_data/season_report_summary.json` (49 records, shape: `{data_mode, record_count, records[]}`)
- **Loaded once** at app startup via FastAPI lifespan. Store in `app.state.store` as indexed dict.
- **Never** re-read from disk per request.
- **Never** modify files in `crop_data/`. Raw CSVs and normalize script belong to Member B.

## Endpoints (frontend depends on these shapes)

```
GET  /health
GET  /api/commodity-groups
GET  /api/commodities?group={group}
GET  /api/commodity-series?group={group}&commodity={commodity}
GET  /api/commodity-insights?group={group}&commodity={commodity}
POST /api/recommendation/{commodity}    → triggers 3-agent AI pipeline
GET  /api/alerts
GET  /demo/canned/{commodity}           → offline fallback (zero external calls)
WS   /ws                                → streams debate events
```

## Out of scope (do not scaffold)

- mandi / district / `arrival_date` columns
- daily forecasting, Prophet, changepoint detection
- transport-cost or profit-margin calculators
- voice pipeline (WhisperFlow, ElevenLabs) — deferred to Phase 6
- SMS alerts, Twilio
- Telugu-language output
- Supabase, Postgres, Redis

If a prompt or doc asks for these, push back — they're explicit non-goals per `.claude/project.md`.

## Conventions

**Module layout**:
```
backend/
  main.py         ← FastAPI app, lifespan, CORS, exception handlers
  config.py       ← Pydantic Settings
  data/           ← loader + Pydantic models
  agents/         ← llm.py + 3 analysts + mediator
  routers/        ← one file per endpoint group
  services/       ← insight_calculator, recommendation_cache
  fallback/       ← canned_responses.py
```

- **All LLM calls** go through `agents/llm.py` — never call Groq SDK directly from a router or agent module. The wrapper handles exponential backoff on 429 and `extract_last_json()` parsing.
- **Parallel agents** run via `asyncio.gather()` with 2s stagger between spawns (spreads TPM load).
- **Recommendation cache**: in-memory dict, 1-hour TTL keyed by commodity name.
- **CORS**: allow only `http://localhost:3000`, registered **before** routers.
- **Secrets**: `.env` file for `GROQ_API_KEY`, never committed. `.env.example` is committed and documents required keys.

## Run commands

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows bash
pip install -r requirements.txt
cp .env.example .env            # then fill in GROQ_API_KEY
uvicorn main:app --reload --port 8000
```

## Smoke tests

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/commodities?group=Oil%20Seeds"
curl "http://localhost:8000/api/commodity-series?group=Cereals&commodity=Cotton"
curl -X POST http://localhost:8000/api/recommendation/Cotton
curl http://localhost:8000/demo/canned/Cotton
```

## Graceful degradation

| Failure | Response |
|---|---|
| Groq 429 rate limit | Return cached result if present; else `503 {"error":"llm_rate_limited"}` |
| LLM returns unparseable JSON | Fall back to deterministic `aggregate_verdicts()` — never return 500 to the frontend |
| All 3 agents fail | Return rule-based recommendation (no AI) with `confidenceLabel: "Low confidence"` |
| Commodity not found | `404 {"error":"commodity_not_found","suggestion": "<closest match>"}` |
| `season_report_summary.json` missing at startup | App refuses to start — log clear error |

## Git

- Current branch: `backend-implementation` (forked from `main`)
- **Do not merge** from `origin/backend` — that branch has a v0 API but we're starting fresh
- `crop_data/` is sourced from `origin/front_data` via `git checkout origin/front_data -- crop_data/`
- Commits touch only `backend/`, `CLAUDE.md`, `plan.md`, and (once) `crop_data/` initial import

## References

- `.claude/project.md` — canonical product specification (v3.0)
- `docs/member_a_backend (1).html` — full Member A role doc (endpoint shapes, agent prompts, TypeScript contracts)
- `plan.md` — phase-by-phase implementation roadmap
