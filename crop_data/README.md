# Crop Data

This folder contains the raw season-wise crop price and arrival reports currently used by KrishiCFO.

## Current Source Files

The checked-in raw reports currently cover these seasons:

- `2022-23`
- `2023-24`
- `2024-25`
- `2025-26`

Each report includes:

- `Commodity Group`
- `Commodity`
- `MSP`
- `Kharif Marketing Season Price`
- `Kharif Marketing Season Arrival`
- `Rabi Marketing Season Price`
- `Rabi Marketing Season Arrival`

## Generated Files

- `season_report_summary.csv`
- `season_report_summary.json`

These files are generated from the raw CSVs by:

```bash
python crop_data/normalize_season_reports.py
```

## Important Notes

- This dataset is season-wise, not mandi-wise.
- It should be used for commodity comparison across seasons.
- Missing values are normalized from `-` to `null` in JSON and empty numeric fields in CSV.
- Raw files should remain unchanged.
