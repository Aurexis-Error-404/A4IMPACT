# KrishiCFO — Season-Wise Commodity Intelligence MVP
## v4.0 — Grounded in Actual Repo State (April 17, 2026)

---

## What This File Is

This is the canonical reference for every contributor. It reflects what is actually built, what the data actually contains, and what the contracts between layers actually are. When this file conflicts with an older PDF, a Slack message, or a verbal agreement — this file wins.

---

## Context

*Problem:* Indian farmers lose significant income each harvest season due to poor visibility into commodity price trends, MSP comparisons, and seasonal arrival patterns — not for lack of data, but because that data is inaccessible and unreadable in their language.

*Solution (Current MVP):* A seasonal commodity intelligence dashboard. Helps users compare MSP, seasonal prices, and seasonal arrivals across four years for 14 major commodities using the season-wise dataset already checked into this repo.

*What changed from v3.0:* The v3.0 plan listed 7 planned frontend components. The actual frontend now has 19 built components, a complete dark glass design system, 3 live routes, and full TypeScript type coverage. The component inventory, repo structure, and type definitions in this document reflect what is actually in front_data.

These files are season-wise commodity reports, not mandi-wise daily market records.

## Build Status (as of April 17, 2026)

| Layer | Status | Notes |
|---|---|---|
| Data normalization | ✅ Complete | 4 CSVs → season_report_summary.json |
| Frontend shell + routes | ✅ Complete | /, /dashboard, /commodity/[slug] |
| Frontend components | ✅ Complete | 19 components, all on canned data |
| TypeScript type system | ✅ Complete | Full contracts in lib/canned-data.ts |
| Design system | ✅ Complete | Dark glass, Fraunces + Lora + Martian Mono |
| FastAPI backend | ❌ Not started | Member A scope |
| AI recommendation layer | ❌ Not started | 3-agent pipeline, Member A scope |
| WebSocket debate stream | ❌ Not started | Member A scope |
| Backend integration in lib/api.ts | ⏳ Blocked | Currently calls canned functions only; blocked on backend |
| Voice pipeline | 🔜 Phase 2 | WhisperFlow + ElevenLabs + 3 parallel agents |

Each CSV has a shared structure:

- `Commodity Group`
- `Commodity`
- `MSP (Rs./Quintal) <season>`
- `Kharif Marketing Season Price (Rs./Quintal)`
- `Kharif Marketing Season Arrival (Metric Tonnes)`
- `Rabi Marketing Season Price (Rs./Quintal)`
- `Rabi Marketing Season Arrival (Metric Tonnes)`

The main commodity groups currently available are:

- `Cereals`
- `Fibre Crops`
- `Oil Seeds`
- `Pulses`

Confirmed commodities across the four season files include:

- `Jowar(Sorghum)`
- `Maize`
- `Paddy(Common)`
- `Cotton`
- `Groundnut`
- `Mustard`
- `Safflower`
- `Sesamum(Sesame,Gingelly,Til)`
- `Soyabean`
- `Sunflower/Sunflower Seed`
- `Arhar(Tur/Red Gram)(Whole)`
- `Bengal Gram(Gram)(Whole)`
- `Black Gram(Urd Beans)(Whole)`
- `Green Gram(Moong)(Whole)`

## Product Direction

### MVP Goal

Build a seasonal commodity dashboard that helps users compare MSP, seasonal prices, and seasonal arrivals across years.

### MVP User Flow

1. Select `commodity_group`
2. Select `commodity`
3. Compare that commodity across available seasons
4. View Kharif and Rabi price and arrival values
5. See simple insights:
   latest season vs MSP, trend direction, highest season, lowest season

### Explicit Non-Goals For This Version

Do not build the current version around:

- `mandi`
- `district`
- `arrival_date`
- daily forecasting
- Prophet
- multi-agent debate
- transport-cost profit estimation

Those can become a later phase only if a new dataset adds date-granular or mandi-level data.

## Working Dataset

Located in crop_data/. Four season-wise commodity reports:

| File | Season |
|---|---|
| Crop_Season_Wise_Price_Arrival_17-04-2026_03-21-29_PM.csv | 2025-26 |
| Crop_Season_Wise_Price_Arrival_17-04-2026_03-25-50_PM.csv | 2024-25 |
| Crop_Season_Wise_Price_Arrival_17-04-2026_03-26-45_PM.csv | 2023-24 |
| Crop_Season_Wise_Price_Arrival_17-04-2026_03-27-50_PM.csv | 2022-23 |

This is *season-wise commodity data* — not mandi-wise, not daily, not date-granular.

### Data Model

Each CSV shares this structure:

| Column | Description |
|---|---|
| Commodity Group | Cereals / Fibre Crops / Oil Seeds / Pulses |
| Commodity | Specific crop name |
| MSP (Rs./Quintal) <season> | Minimum Support Price for the season |
| Kharif Marketing Season Price (Rs./Quintal) | Average Kharif price |
| Kharif Marketing Season Arrival (Metric Tonnes) | Kharif arrival volume |
| Rabi Marketing Season Price (Rs./Quintal) | Average Rabi price |
| Rabi Marketing Season Arrival (Metric Tonnes) | Rabi arrival volume |

### Commodity Groups and Confirmed Commodities

*Cereals:* Jowar (Sorghum), Maize, Paddy (Common)

*Fibre Crops:* Cotton

*Oil Seeds:* Groundnut, Mustard, Safflower, Sesamum (Sesame, Gingelly, Til), Soyabean, Sunflower / Sunflower Seed

*Pulses:* Arhar (Tur / Red Gram)(Whole), Bengal Gram (Gram)(Whole), Black Gram (Urd Beans)(Whole), Green Gram (Moong)(Whole)

### Normalized Record Shape

```json
{
  "season_year": "2025-26",
  "commodity_group": "Oil Seeds",
  "commodity": "Groundnut",
  "msp": 7263.0,
  "kharif_price": 5066.59,
  "kharif_arrival_tonnes": 252.07,
  "rabi_price": null,
  "rabi_arrival_tonnes": null,
  "source_file": "Crop_Season_Wise_Price_Arrival_17-04-2026_03-21-29_PM.csv"
}
```

Missing values: raw `-` becomes null in JSON, empty field in CSV. Raw CSV files are never modified.

---

## TypeScript Type System

These types live in frontend/lib/canned-data.ts and are the *canonical contracts* for every layer. The backend must return shapes compatible with these types. Do not change these without updating both the backend contract and the frontend simultaneously.

```ts
// Primitive union types — use exact string values, no case variations
type SeasonAvailability  = "Kharif only" | "Rabi only" | "Both" | "Sparse";
type RiskLevel           = "Low" | "Watch" | "High";
type TrendDirection      = "up" | "down" | "flat";
type RecommendationLabel = "Hold" | "Lean sell" | "Defer" | "Protect";

// Raw normalized record — maps 1:1 to season_report_summary.json
type SeasonPriceRecord = {
  season_year: string;
  commodity_group: string;
  commodity: string;
  msp: number | null;
  kharif_price: number | null;
  kharif_arrival_tonnes: number | null;
  rabi_price: number | null;
  rabi_arrival_tonnes: number | null;
  source_file: string;
};

// Full computed insight shape — consumed by RecommendationCard, RiskPanel,
// HeroCanvas, MSPComparisonRail, and the commodity detail page
type CommodityInsightSummary = {
  commodity: string;
  group: string;
  latestSeason: string;
  latestMsp: number | null;
  latestReferencePrice: number | null;
  latestDelta: number;
  latestDeltaPct: number;           // decimal e.g. 0.12 = 12%. NOT 12.
  latestDeltaLabel: string;
  highestSeason: string;
  highestPriceLabel: string;
  priceTrend: TrendDirection;
  trendChangePct: number;
  seasonAvailability: SeasonAvailability;
  kharifShare: number;
  rabiShare: number;
  riskLevel: RiskLevel;
  recommendationLabel: RecommendationLabel;
  confidenceLabel: string;          // "High confidence" | "Moderate confidence" | "Low confidence"
  recommendationRationale: string;
};

// Alert item — consumed by AlertSeverityStack
type AlertItem = {
  id: string;
  severity: "red" | "amber" | "green";
  commodity: string;
  group: string;
  headline: string;
  detail: string;
  season: string;
};

// Pulse feed event — consumed by MarketPulseFeed
type PulseEvent = {
  id: string;
  commodity: string;
  group: string;
  season: string;
  deltaLabel: string;
  delta: number;
  label: string;
  timeAgo: string;
};

// Compact card shape — used on dashboard commodity grid
type CommodityCardSummary = {
  slug: string;
  commodity: string;
  group: string;
  latestSeason: string;
  latestReferencePrice: number | null;
  latestMsp: number | null;
  latestDeltaPct: number;
  riskLevel: RiskLevel;
  seasonAvailability: SeasonAvailability;
  recommendationLabel: RecommendationLabel;
  priceTrend: TrendDirection;
};

// Top-level dashboard payload
type DashboardSummary = {
  dataMode: string;              // always "seasonal_commodity" for this version
  totalCommodities: number;
  totalGroups: number;
  spotlight: CommodityCardSummary | null;
};
```

*Strict mode is on.* String union literals are case-sensitive. "lean sell" is a type error. "HOLD" is a type error. latestDeltaPct: 12 is a type error — must be 0.12.

---

## Insight Logic

Computed in lib/canned-data.ts for every commodity. The backend must replicate this exactly when serving CommodityInsightSummary.

| Field | Computation |
|---|---|
| latestReferencePrice | kharif_price for Kharif-bearing seasons; rabi_price for Rabi-only commodities |
| latestDelta | latestReferencePrice - latestMsp |
| latestDeltaPct | latestDelta / latestMsp — decimal |
| priceTrend | Compare last two seasons' reference price: up / down / flat (±3% threshold) |
| trendChangePct | (current - previous) / previous — decimal |
| seasonAvailability | Derived from which season fields are non-null across all 4 records |
| kharifShare | Fraction of 4 seasons where kharif_price is non-null |
| rabiShare | Fraction of 4 seasons where rabi_price is non-null |
| riskLevel | "High" if latestDeltaPct < -0.05; "Watch" if within ±5% of MSP; "Low" otherwise |
| highestSeason | Season with highest latestReferencePrice across all 4 years |

*Recommendation label mapping:*

| riskLevel | priceTrend | recommendationLabel |
|---|---|---|
| Low | up | Hold |
| Low | flat | Hold |
| Low | down | Defer |
| Watch | up | Lean sell |
| Watch | flat | Lean sell |
| Watch | down | Defer |
| High | any | Protect |

---

## Design System

The frontend uses a dark glass aesthetic. Do not deviate without team agreement.

```css
/* Core CSS variables — globals.css */
--bg:     #0f120e;                          /* page background */
--ink:    #f4f0e7;                          /* primary text */
--muted:  #acb2a4;                          /* secondary text */
--gold:   #ef9f27;                          /* primary accent */
--olive:  #639922;                          /* success / positive */
--teal:   #1d9e75;                          /* data / metric */
--red:    #e24b4a;                          /* risk / negative */
--violet: #7f77dd;                          /* AI / agent layer */
--panel:  rgba(255, 255, 255, 0.055);
--border: rgba(255, 255, 255, 0.08);
--shadow: 0 24px 90px rgba(0, 0, 0, 0.42);
--ease:   cubic-bezier(0.22, 1, 0.36, 1);
```

*Fonts (loaded via next/font/google in layout.tsx):*
- Fraunces — display headings, hero titles, large numerics
- Lora — body text, card copy, prose
- Martian Mono — labels, metadata, code, tags, nav links, KPI values

*Panels:* border: 1px solid rgba(255,255,255,0.06), border-radius: 24px, backdrop-filter: blur(28px), background: rgba(255,255,255,0.03).

*Background:* body::before applies a blurred, darkened bg.jpg at fixed position via filter: blur(12px) brightness(0.35).

---

## Repo Structure (Actual)

```
A4IMPACT/
├── .claude/
│   ├── project.md                             ← this file
│   └── settings.json
├── crop_data/
│   ├── Crop_Season_Wise_...03-21-29_PM.csv    ← 2025-26 raw (do not modify)
│   ├── Crop_Season_Wise_...03-25-50_PM.csv    ← 2024-25 raw (do not modify)
│   ├── Crop_Season_Wise_...03-26-45_PM.csv    ← 2023-24 raw (do not modify)
│   ├── Crop_Season_Wise_...03-27-50_PM.csv    ← 2022-23 raw (do not modify)
│   ├── normalize_season_reports.py            ← merges all 4 CSVs into one dataset
│   ├── season_report_summary.csv              ← generated flat output
│   ├── season_report_summary.json             ← generated structured output; used by frontend
│   ├── data_dictionary.md                     ← field definitions
│   └── README.md
├── Project_role/
│   ├── KrishiCFO · Member B · Data + Frontend · 24h Roadmap.pdf
│   └── member-b-execution-plan.md
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                         ← Fraunces + Lora + Martian Mono, imports globals.css
│   │   ├── globals.css                        ← full design system + all component CSS
│   │   ├── page.tsx                           ← landing page with hero + spotlight card
│   │   ├── dashboard/
│   │   │   └── page.tsx                       ← main commodity intelligence dashboard
│   │   └── commodity/
│   │       └── [slug]/
│   │           └── page.tsx                   ← commodity detail route
│   ├── components/
│   │   ├── TopNav.tsx
│   │   ├── HeroCanvas.tsx
│   │   ├── CommodityGroupSelector.tsx
│   │   ├── CommoditySelector.tsx
│   │   ├── CommodityFilterBar.tsx
│   │   ├── SeasonPriceChart.tsx
│   │   ├── SeasonArrivalChart.tsx
│   │   ├── SeasonalComparisonPanel.tsx
│   │   ├── SeasonAvailabilityBand.tsx
│   │   ├── SeasonSplitBar.tsx
│   │   ├── MSPComparisonCard.tsx
│   │   ├── PriceDeviationGauge.tsx
│   │   ├── RiskPanel.tsx
│   │   ├── RecommendationCard.tsx             ← needs real backend AI data
│   │   ├── AlertSeverityStack.tsx
│   │   ├── MarketPulseFeed.tsx
│   │   ├── CommoditySummaryTable.tsx
│   │   ├── TrendArrowBadge.tsx
│   │   ├── CommodityDetailNav.tsx
│   │   └── VoiceButton.tsx                    ← Phase 2 only; not yet wired
│   ├── lib/
│   │   ├── canned-data.ts                     ← all types + all data functions
│   │   └── api.ts                             ← fetch wrappers; currently calls canned functions only
│   ├── public/
│   ├── .env.example                           ← NEXT_PUBLIC_API_URL=http://localhost:8000
│   ├── next.config.mjs
│   ├── package.json                           ← Next.js 14.2, React 18, TypeScript 5.4
│   └── tsconfig.json                          ← strict: true, moduleResolution: bundler
├── .gitignore
└── package-lock.json
```

---

## Frontend Component Inventory

| Component | Status | Consumes | Notes |
|---|---|---|---|
| TopNav.tsx | ✅ Built | — | Pill nav, gold brand mark, Martian Mono links |
| HeroCanvas.tsx | ✅ Built | CommodityInsightSummary | Hero headline + trend badge + key metrics |
| CommodityGroupSelector.tsx | ✅ Built | groups list | Drives all other components |
| CommoditySelector.tsx | ✅ Built | commodities list | Filtered by selected group |
| CommodityFilterBar.tsx | ✅ Built | both selectors | Combined filter bar for dashboard |
| SeasonPriceChart.tsx | ✅ Built | SeasonPriceRecord[] | 4-season price chart, custom SVG paths |
| SeasonArrivalChart.tsx | ✅ Built | SeasonPriceRecord[] | Arrival volume bar chart |
| SeasonalComparisonPanel.tsx | ✅ Built | SeasonPriceRecord[], CommodityInsightSummary | Cross-season comparison |
| SeasonAvailabilityBand.tsx | ✅ Built | SeasonAvailability | Kharif / Rabi / Both / Sparse indicator |
| SeasonSplitBar.tsx | ✅ Built | kharifShare, rabiShare | Kharif vs Rabi proportion bar |
| MSPComparisonCard.tsx | ✅ Built | CommodityInsightSummary | MSP floor + deviation gauge + KPI rail |
| PriceDeviationGauge.tsx | ✅ Built | latestDeltaPct | Visual gauge for MSP floor distance |
| RiskPanel.tsx | ✅ Built | CommodityInsightSummary | Low/Watch/High badge + risk-item grid |
| RecommendationCard.tsx | ⚡ Needs AI | CommodityInsightSummary | Shell renders canned label/rationale. Needs real /api/recommendation from backend. |
| AlertSeverityStack.tsx | ✅ Built | AlertItem[] | Red/amber/green stacked alert cards |
| MarketPulseFeed.tsx | ✅ Built | PulseEvent[] | Pulse event feed, currently canned |
| CommoditySummaryTable.tsx | ✅ Built | SeasonPriceRecord[] | 4-season tabular view |
| TrendArrowBadge.tsx | ✅ Built | TrendDirection | Up / down / flat indicator |
| CommodityDetailNav.tsx | ✅ Built | slug | Tab navigation for /commodity/[slug] |
| VoiceButton.tsx | 🔜 Phase 2 | /voice/query | MediaRecorder → WhisperFlow → ElevenLabs |

## Backend Scope

The backend does not yet exist. Member A owns it entirely. It runs at localhost:8000.

### Stack

```
Python FastAPI
uvicorn --host 0.0.0.0 --port 8000
In-memory dict from season_report_summary.json (no database required)
Groq Llama 3.1 8B — AI recommendation and agent layer
```

### CORS

Must be registered *before* all routes in main.py:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Surface

```
GET  /health
GET  /api/commodities
GET  /api/season-data/{commodity}
GET  /api/insights/{commodity}
POST /api/recommendation/{commodity}    ← 3 agents + mediator → CommodityInsightSummary
WS   /ws                                ← streams agent events with 2s stagger
GET  /api/alerts
GET  /demo/canned/{commodity}           ← offline pre-computed, zero external calls
POST /voice/query                       ← Phase 2: WhisperFlow + 3 agents + ElevenLabs
POST /voice/transcribe                  ← Phase 2: STT only
```

### AI Recommendation Layer

RecommendationCard and RiskPanel are powered by 3 parallel Llama 8B agents that run via asyncio.gather():

- *Season-Optimist* — looks for price-above-MSP seasons, Kharif uptrend signals, highest price year
- *Season-Pessimist* — looks for price-below-MSP events, declining arrival volumes, glut patterns
- *Risk Analyst* — MSP floor proximity, Kharif/Rabi coverage risk, sparse-data commodity flags

A Llama 8B *Mediator* synthesizes all three verdicts into the CommodityInsightSummary shape. The mediator output fields must match the TypeScript union types exactly — see the critical field constraints table below.

### WebSocket Event Contract

```json
{"stage":"optimist",  "data":{"verdict":"HOLD",     "confidence":72, "reasoning":"..."}, "ts":"..."}
{"stage":"pessimist", "data":{"verdict":"LEAN_SELL", "confidence":65, "reasoning":"..."}, "ts":"..."}
{"stage":"risk",      "data":{"verdict":"WATCH",     "risk_level":"High", "reasoning":"..."}, "ts":"..."}
{"stage":"mediator",  "data":{"recommendationLabel":"Hold", "confidenceLabel":"Moderate confidence", "recommendationRationale":"...", "conflict_score":"MEDIUM", ...}}
```

The mediator stage data field must include all remaining CommodityInsightSummary fields so the frontend can fully hydrate RecommendationCard and RiskPanel from a single WebSocket connection.

---

## Frontend ↔ Backend Integration Contract

lib/api.ts currently delegates all calls to canned functions. When the backend is ready, each function becomes a fetch() call to localhost:8000. The canned path must remain as the ?demo=canned fallback — it is not removed, it is bypassed.

### Critical field constraints (TypeScript strict mode failures if wrong)

| Field | Must be | Must NOT be |
|---|---|---|
| recommendationLabel | "Lean sell" | "LEAN_SELL", "lean sell", "Lean Sell" |
| riskLevel | "High" | "HIGH", "high", "RISK_HIGH" |
| latestDeltaPct | 0.12 (decimal fraction) | 12 (whole percent) |
| priceTrend | "up" \| "down" \| "flat" | "UP", "rising", "increasing" |
| seasonAvailability | "Kharif only" | "kharif", "KHARIF_ONLY", "kharif only" |
| confidenceLabel | "High confidence" | "HIGH_CONFIDENCE", "high", "High" |

## Environment Variables

```bash
# frontend/.env.example (committed)
NEXT_PUBLIC_API_URL=http://localhost:8000

# backend/.env (to be created by Member A, not committed)
GROQ_API_KEY=...
ELEVENLABS_API_KEY=...       # Phase 2 only
WHISPER_API_KEY=...          # Phase 2 only
```

- `district`
- `mandi`
- `arrival_date`
- daily modal prices

## Explicit Non-Goals for Current Phase

Do *not* build the following until a new dataset adds date-granular or mandi-level data:

- mandi or district filtering
- arrival_date time series
- Daily price forecasting (Prophet or otherwise)
- Transport-cost profit estimation
- Twilio SMS alerts
- ChoroplethMap / geospatial views
- Telugu language output

These are a later phase, contingent on new data.

---

## Phase 2 — Voice Pipeline (Planned, Not Started)

Activated only after the backend AI recommendation layer is stable and all integration contracts are passing.

*Planned stack:*

```
Browser MediaRecorder  (WAV blob, multipart/form-data POST)
  ↓
WhisperFlow STT        language="te" · ~0.8s · fallback: Groq Whisper Large v3
  ↓
3× Llama 8B Parallel   Season-Optimist + Season-Pessimist + Risk Analyst · ~1.4s
  ↓
Llama 8B Synthesizer   merges 3 verdicts → Telugu advisory paragraph · ~0.7s
  ↓
ElevenLabs Multilingual v2 TTS   Telugu text → audio_base64 · 5s timeout · ~0.9s

Target: <3s text response · <7s with audio
```

*Key decisions locked for Phase 2:*
- ElevenLabs replaces Bhashini (no 24h registration) and AI4Bharat (no 300MB local model)
- 3 parallel agents mirror the dashboard debate — same architecture, not a shortcut
- VoiceButton.tsx shell already exists; wire to /voice/query when ready
- Pre-generate 3 Telugu fallback audio clips at Phase 2 Hour 0 before writing any code

*Backend endpoint:*

```
POST /voice/query
  accepts: multipart/form-data, field "audio" (WAV blob)
  returns: {
    "text_response_te": "...",
    "audio_base64": "..." | null,
    "commodity_detected": "Cotton"
  }
```

Text response is always returned. audio_base64 is nullable — VoiceButton.tsx handles both states.

---

## Success Criteria

### Phase 1 — Complete when all of the following are true:

1. season_report_summary.json is clean and all 14 commodities are verified ✅
2. Dashboard filters by commodity group and commodity ✅
3. Charts and MSP comparison render across all 4 seasons ✅
4. RecommendationCard shows real AI verdicts from backend — not canned data ⏳
5. WebSocket streams 4 agent cards sequentially to the dashboard ⏳
6. /demo/canned/{commodity} returns correct pre-computed data with zero external API calls ⏳
7. No TypeScript errors in lib/api.ts after backend integration swap ⏳

### Phase 2 — Complete when all of the following are true:

1. Telugu voice query returns Telugu text within 3 seconds
2. ElevenLabs audio plays within 7 seconds, or text-only fallback works silently
3. VoiceButton.tsx handles mic permission denial, no-mic devices, and network errors without crashing

---

## Data Mode Contract

All API responses and the top-level DashboardSummary include dataMode: "seasonal_commodity". This field exists so the app can later support a mandi_daily mode without redesigning the data layer. Do not hardcode assumptions that only seasonal data will ever exist.

---

KrishiCFO · project.md · v4.0 · integration branch · Last updated April 18, 2026
