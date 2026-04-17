import csv
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = BASE_DIR / "season_report_summary.csv"
OUTPUT_JSON = BASE_DIR / "season_report_summary.json"


def parse_number(value: str):
    value = (value or "").strip()
    if value in {"", "-"}:
        return None
    return float(value)


def extract_season_year(report_label: str) -> str:
    match = re.search(r"\((\d{4}-\d{2})\)", report_label or "")
    if not match:
        raise ValueError(f"Could not extract season year from: {report_label!r}")
    return match.group(1)


def load_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 4:
        raise ValueError(f"{csv_path.name} does not contain expected report rows")

    report_label = rows[0][3].strip() if len(rows[0]) > 3 else ""
    season_year = extract_season_year(report_label)
    data_rows = [row for row in rows[3:] if any(cell.strip() for cell in row)]

    normalized = []
    for row in data_rows:
        padded = row + [""] * (7 - len(row))
        normalized.append(
            {
                "season_year": season_year,
                "commodity_group": padded[0].strip(),
                "commodity": padded[1].strip(),
                "msp": parse_number(padded[2]),
                "kharif_price": parse_number(padded[3]),
                "kharif_arrival_tonnes": parse_number(padded[4]),
                "rabi_price": parse_number(padded[5]),
                "rabi_arrival_tonnes": parse_number(padded[6]),
                "source_file": csv_path.name,
            }
        )

    return normalized


def build_summary():
    records = []
    for csv_path in sorted(BASE_DIR.glob("*.csv")):
        records.extend(load_rows(csv_path))

    records.sort(key=lambda item: (item["commodity_group"], item["commodity"], item["season_year"]))
    return records


def write_csv(records):
    fieldnames = [
        "season_year",
        "commodity_group",
        "commodity",
        "msp",
        "kharif_price",
        "kharif_arrival_tonnes",
        "rabi_price",
        "rabi_arrival_tonnes",
        "source_file",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_json(records):
    payload = {
        "data_mode": "seasonal_commodity",
        "record_count": len(records),
        "records": records,
    }
    with OUTPUT_JSON.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main():
    records = build_summary()
    write_csv(records)
    write_json(records)
    print(f"Wrote {len(records)} records to {OUTPUT_CSV.name} and {OUTPUT_JSON.name}")


if __name__ == "__main__":
    main()
