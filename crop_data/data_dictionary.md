# Data Dictionary

## Normalized Fields

- `season_year`
  Season label extracted from the report, such as `2025-26`.

- `commodity_group`
  High-level crop grouping from the source report, such as `Cereals` or `Pulses`.

- `commodity`
  Exact commodity name from the source file.

- `msp`
  Minimum Support Price for that season in rupees per quintal.

- `kharif_price`
  Reported Kharif season price in rupees per quintal.

- `kharif_arrival_tonnes`
  Reported Kharif season arrivals in metric tonnes.

- `rabi_price`
  Reported Rabi season price in rupees per quintal.

- `rabi_arrival_tonnes`
  Reported Rabi season arrivals in metric tonnes.

- `source_file`
  Raw CSV filename used to create the normalized record.

## Missing Values

The raw files use `-` for missing values.

Normalization rules:

- `-` becomes `null` in JSON
- `-` becomes an empty field in generated CSV output

## Data Mode

The current project should treat this dataset as:

- `seasonal_commodity`

It is not:

- mandi-level
- district-level
- daily time-series data
