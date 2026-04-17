# KrishiCFO Member B Execution Plan

## Assigned Role

Member B owns:

- data cleanup and normalization
- frontend data integration
- dataset-to-UI contract design

For the current repo state, this means Member B should build around the checked-in season-wise crop data, not around mandi-level forecasting.

## Current Dataset Reality

As of April 17, 2026, `crop_data/` contains four checked-in season reports:

- `2022-23`
- `2023-24`
- `2024-25`
- `2025-26`

The file structure is:

- `Commodity Group`
- `Commodity`
- `MSP`
- `Kharif Price`
- `Kharif Arrival`
- `Rabi Price`
- `Rabi Arrival`

This is enough to build a strong commodity intelligence dashboard.

This is not enough to build:

- mandi filters
- daily time-series forecasting
- transport/profit logic by location

## What Member B Should Build

### Data Layer

Create a cleaned unified dataset with this shape:

- `season_year`
- `commodity_group`
- `commodity`
- `msp`
- `kharif_price`
- `kharif_arrival_tonnes`
- `rabi_price`
- `rabi_arrival_tonnes`

### Frontend Layer

Build the dashboard around:

- `commodity_group`
- `commodity`
- season comparison
- MSP vs seasonal price
- Kharif vs Rabi arrival visibility

## Best Product Direction For This Dataset

The best version of the product right now is:

- a season-wise crop intelligence dashboard

It should answer:

- how a commodity performed across seasons
- whether seasonal price was above or below MSP
- whether Kharif or Rabi activity existed for that commodity
- which season was strongest or weakest

It should not yet answer:

- which mandi is best
- when to sell this week
- how prices move by date

## Implementation Deliverables

### In `crop_data/`

- `normalize_season_reports.py`
- `season_report_summary.csv`
- `season_report_summary.json`
- `README.md`
- `data_dictionary.md`

### In `frontend/`

- `app/page.tsx`
- `app/dashboard/page.tsx`
- `components/CommodityGroupSelector.tsx`
- `components/CommoditySelector.tsx`
- `components/SeasonPriceChart.tsx`
- `components/SeasonArrivalChart.tsx`
- `components/MSPComparisonCard.tsx`
- `components/CommoditySummaryTable.tsx`
- `components/InsightCards.tsx`
- `lib/canned-data.ts`
- `lib/api.ts`

## 24-Hour Execution Order

### Hour 0-2

- inspect all four CSV files
- normalize the data
- generate merged CSV and JSON outputs
- document all fields and commodity coverage

Success at Hour 2:

- merged dataset exists
- field definitions are documented
- data is ready for frontend use

### Hour 2-6

- scaffold the frontend
- build commodity group selector
- build commodity selector
- build season price chart
- build season arrival chart

Success at Hour 6:

- UI renders real cleaned data
- group and commodity filters work

### Hour 6-10

- build MSP comparison card
- build summary table
- build insight cards
- add empty-state and loading-state handling

Success at Hour 10:

- the dashboard tells a useful story for each commodity

### Hour 10-14

- create `lib/api.ts`
- route components through one data access layer
- keep local JSON as default source
- prepare for a future backend wrapper without component rewrites

Success at Hour 14:

- local and future API modes are structurally supported

### Hour 14-20

- responsive pass
- chart polish
- copy polish
- improve labels for Kharif and Rabi sections

### Hour 20-24

- lock the demo flow
- test all commodity groups
- fix visible blockers only
- prepare backup screenshots or recording

## Data Rules

- keep source commodity names exactly as-is
- keep raw files untouched
- convert `-` to `null`
- parse numbers to numeric values
- preserve Kharif and Rabi as separate fields
- do not fabricate districts, mandis, or dates

## Frontend Contract Recommendation

Member B should align with backend on this record shape:

```json
{
  "season_year": "2025-26",
  "commodity_group": "Pulses",
  "commodity": "Bengal Gram(Gram)(Whole)",
  "msp": 5650.0,
  "kharif_price": null,
  "kharif_arrival_tonnes": null,
  "rabi_price": 5942.31,
  "rabi_arrival_tonnes": 18.42
}
```

## What To Cut If Time Gets Tight

Cut in this order:

- advanced motion
- extra insight cards
- backend wrapper if local JSON already works

Do not cut:

- normalization script
- merged dataset
- group and commodity filters
- price chart
- arrival chart
- MSP comparison

## Immediate Recommendation

Start with the data layer first.

The highest-value sequence is:

1. normalize all four season reports
2. generate merged outputs
3. build the frontend on cleaned local JSON
4. add a thin API layer only if needed afterward
