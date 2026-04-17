"""Load season-wise commodity CSVs into an in-memory indexed store.

Source file shape (one file per season year):

    Row 1: ",,,Season Price & Arrival Report (2025-26),,,"
    Row 2: subheader spanning Kharif/Rabi
    Row 3: column header ("Commodity Group, Commodity, MSP ..., Kharif Price, ..., Rabi Price, ...")
    Row 4+: data
    Trailing blank rows

Rules enforced here:
- season_year extracted from the parenthesised token in row 1.
- A commodity has EITHER a Kharif price OR a Rabi price (never both in the samples we've
  seen). season_price = whichever is non-null. If both happen to be present in future data,
  Kharif wins (noted so the contract stays deterministic).
- msp coerces to int (rupee integer). season_price coerces to float.
- Null-like strings ("-", "", "NA", "null", "None", case-insensitive) become None.
- Commodity and group names are preserved byte-for-byte (no trimming of internal content,
  only leading/trailing whitespace stripped — CSV may pad cells).
"""
from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_SEASON_YEAR_RE = re.compile(r"\((\d{4}-\d{2})\)")
_NULL_TOKENS = {"", "-", "na", "null", "none"}


@dataclass(frozen=True)
class Row:
    season_year: str
    commodity_group: str
    commodity: str
    msp: Optional[int]
    season_price: Optional[float]


@dataclass
class Store:
    rows: list[Row]
    groups: list[str]  # alphabetical
    commodities_by_group: dict[str, list[str]]  # each alphabetical
    series_by_key: dict[tuple[str, str], list[Row]]  # pre-sorted ascending by season_year


def _parse_nullable_number(raw: str) -> Optional[float]:
    if raw is None:
        return None
    token = raw.strip()
    if token.lower() in _NULL_TOKENS:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def _parse_season_year(first_row_cells: list[str]) -> Optional[str]:
    joined = " ".join(c for c in first_row_cells if c)
    match = _SEASON_YEAR_RE.search(joined)
    return match.group(1) if match else None


def _season_year_sort_key(season_year: str) -> int:
    # "2022-23" -> 2022. Safe because the format is rigid in the source.
    return int(season_year.split("-", 1)[0])


def _load_one_file(path: Path) -> list[Row]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows_raw = list(reader)

    if len(rows_raw) < 4:
        log.warning("skipping %s: fewer than 4 rows", path.name)
        return []

    season_year = _parse_season_year(rows_raw[0])
    if not season_year:
        # Fallback: derive from filename stem if it matches the pattern.
        match = re.match(r"(\d{4}-\d{2})", path.stem)
        if not match:
            log.warning("skipping %s: no season_year in header or filename", path.name)
            return []
        season_year = match.group(1)

    out: list[Row] = []
    dropped: list[str] = []
    for raw in rows_raw[3:]:
        # Skip trailing/empty rows.
        if not any(cell.strip() for cell in raw):
            continue
        if len(raw) < 6:
            dropped.append(",".join(raw))
            continue

        group = raw[0].strip()
        commodity = raw[1].strip()
        if not group or not commodity:
            dropped.append(",".join(raw))
            continue

        msp_raw = _parse_nullable_number(raw[2])
        kharif_price = _parse_nullable_number(raw[3]) if len(raw) > 3 else None
        rabi_price = _parse_nullable_number(raw[5]) if len(raw) > 5 else None

        # Kharif wins if both somehow appear; else whichever is non-null; else null.
        season_price = kharif_price if kharif_price is not None else rabi_price

        out.append(
            Row(
                season_year=season_year,
                commodity_group=group,
                commodity=commodity,
                msp=int(msp_raw) if msp_raw is not None else None,
                season_price=season_price,
            )
        )

    if dropped:
        log.warning(
            "dropped %d malformed rows from %s; first examples: %s",
            len(dropped),
            path.name,
            dropped[:3],
        )
    return out


def load_dataset(data_dir: Path) -> Store:
    if not data_dir.exists():
        log.warning("data dir %s does not exist; starting with empty store", data_dir)
        return Store(rows=[], groups=[], commodities_by_group={}, series_by_key={})

    all_rows: list[Row] = []
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        log.warning("no CSV files in %s; starting with empty store", data_dir)
        return Store(rows=[], groups=[], commodities_by_group={}, series_by_key={})

    for path in csv_files:
        all_rows.extend(_load_one_file(path))

    # Build indexes.
    groups_set: set[str] = set()
    commodities_by_group: dict[str, set[str]] = {}
    series_by_key: dict[tuple[str, str], list[Row]] = {}

    for row in all_rows:
        groups_set.add(row.commodity_group)
        commodities_by_group.setdefault(row.commodity_group, set()).add(row.commodity)
        series_by_key.setdefault((row.commodity_group, row.commodity), []).append(row)

    groups_sorted = sorted(groups_set)
    commodities_sorted = {g: sorted(cs) for g, cs in commodities_by_group.items()}
    for key, series in series_by_key.items():
        series.sort(key=lambda r: _season_year_sort_key(r.season_year))

    log.info(
        "loaded %d rows across %d groups and %d commodities from %d files",
        len(all_rows),
        len(groups_sorted),
        sum(len(v) for v in commodities_sorted.values()),
        len(csv_files),
    )

    return Store(
        rows=all_rows,
        groups=groups_sorted,
        commodities_by_group=commodities_sorted,
        series_by_key=series_by_key,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else "backend/data/seasons")
    store = load_dataset(target)
    print(f"rows={len(store.rows)} groups={store.groups}")
    for group, items in store.commodities_by_group.items():
        print(f"  {group}: {items}")
