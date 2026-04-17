import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Store:
    records: list[dict]
    groups: list[str]
    commodities_by_group: dict[str, list[str]]
    # key: (commodity_group, commodity) → records sorted by season_year ascending
    series_by_key: dict[tuple[str, str], list[dict]] = field(default_factory=dict)


def load(path: str | Path) -> Store:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. "
            "Run crop_data/normalize_season_reports.py or pull from origin/front_data."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    records: list[dict] = raw["records"]

    groups_seen: set[str] = set()
    commodities_by_group: dict[str, set[str]] = {}
    series_by_key: dict[tuple[str, str], list[dict]] = {}

    for r in records:
        g: str = r["commodity_group"]
        c: str = r["commodity"]
        groups_seen.add(g)
        commodities_by_group.setdefault(g, set()).add(c)
        series_by_key.setdefault((g, c), []).append(r)

    for key in series_by_key:
        series_by_key[key].sort(key=lambda r: r["season_year"])

    return Store(
        records=records,
        groups=sorted(groups_seen),
        commodities_by_group={g: sorted(cs) for g, cs in commodities_by_group.items()},
        series_by_key=series_by_key,
    )
