# KrishiCFO MVP Implementation Plan
## Season-Wise Commodity Intelligence Version

## Context

KrishiCFO is currently being built around the crop dataset that is already checked into this repo.

As of April 17, 2026, the working data in `crop_data/` is:

- `Crop_Season_Wise_Price_Arrival_17-04-2026_03-27-50_PM.csv` → `2022-23`
- `Crop_Season_Wise_Price_Arrival_17-04-2026_03-26-45_PM.csv` → `2023-24`
- `Crop_Season_Wise_Price_Arrival_17-04-2026_03-25-50_PM.csv` → `2024-25`
- `Crop_Season_Wise_Price_Arrival_17-04-2026_03-21-29_PM.csv` → `2025-26`

These files are season-wise commodity reports, not mandi-wise daily market records.

That means the current MVP should be a commodity intelligence dashboard, not a mandi forecasting product.

## Current Data Model

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

## Architecture

### Current Stack

```text
Next.js frontend
  ↕
FastAPI backend
  ↕
Cleaned JSON / CSV seasonal commodity dataset
```

### Data Mode

The current app should operate in:

- `seasonal_commodity` mode

This should be reflected in the API and frontend contracts so the app can support a future `mandi_daily` mode later without a redesign.

## Frontend Scope

### Core Pages

- `frontend/app/page.tsx`
- `frontend/app/dashboard/page.tsx`

### Core Components

- `CommodityGroupSelector.tsx`
- `CommoditySelector.tsx`
- `SeasonPriceChart.tsx`
- `SeasonArrivalChart.tsx`
- `MSPComparisonCard.tsx`
- `CommoditySummaryTable.tsx`
- `InsightCards.tsx`

### Frontend Behavior

- use local cleaned JSON first
- optionally swap to API later through `lib/api.ts`
- show loading, success, and error states
- avoid implying data granularity that does not exist

## Backend Scope

### Recommended Core Routes

```text
GET /health
GET /commodity-groups
GET /commodities?group=<group>
GET /commodity-series?group=<group>&commodity=<commodity>
GET /commodity-insights?group=<group>&commodity=<commodity>
```

### Response Model

Each record should normalize to:

```json
{
  "season_year": "2025-26",
  "commodity_group": "Oil Seeds",
  "commodity": "Groundnut",
  "msp": 7263.0,
  "kharif_price": 5066.59,
  "kharif_arrival_tonnes": 252.07,
  "rabi_price": null,
  "rabi_arrival_tonnes": null
}
```

## Repo Structure Target

```text
A4IMPACT/
  .claude/
    project.md
  crop_data/
    raw CSV files
    normalize_season_reports.py
    season_report_summary.csv
    season_report_summary.json
    data_dictionary.md
    README.md
  Project_role/
    member-b-execution-plan.md
  frontend/
    app/
    components/
    lib/
```

## Implementation Priorities

### Priority 1

- normalize the raw CSV files
- generate one merged machine-readable dataset
- document the fields clearly

### Priority 2

- scaffold the frontend
- build group and commodity selectors
- render season-wise price and arrival charts

### Priority 3

- add insight cards
- add API wrappers
- add backend endpoints if needed

## Data Cleaning Rules

- keep source commodity names unchanged
- keep raw CSV files untouched
- convert `-` to `null`
- parse all numeric values as numbers
- infer `season_year` from the report label in the file
- preserve Kharif and Rabi separately

## Execution Order

### Step 1

Clean and merge the seasonal crop files.

### Step 2

Generate reusable JSON and CSV outputs for frontend and backend.

### Step 3

Create the frontend shell around `commodity_group` and `commodity`.

### Step 4

Render chart and summary views from the cleaned data.

### Step 5

Only after that, decide whether a thin backend wrapper is necessary.

## Success Criteria

The current MVP is successful if:

- the repo contains a clean merged dataset
- the dashboard can filter by commodity group and commodity
- users can compare MSP, price, and arrival across seasons
- the UI does not pretend to have mandi-level or daily forecasting data

## Future Extension

If a future dataset includes:

- `district`
- `mandi`
- `arrival_date`
- daily modal prices

then KrishiCFO can add:

- forecast views
- location filters
- profit estimation
- debate and advisory layers

That is a later phase, not the current implementation target.
