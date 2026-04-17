"""Pure query functions over the in-memory Store. No FastAPI imports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.data.loader import Row, Store


class NotFound(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MissingParam(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class SeriesRecord:
    season_year: str
    msp: Optional[int]
    season_price: Optional[float]


@dataclass
class Insights:
    commodity_group: str
    commodity: str
    highest_season: Optional[str]
    lowest_season: Optional[str]
    latest_delta_from_msp: Optional[float]
    latest_delta_percent: Optional[float]
    price_trend: str  # "up" | "down" | "flat"


def list_groups(store: Store) -> list[str]:
    return list(store.groups)


def list_commodities(store: Store, group: str) -> list[str]:
    if group not in store.commodities_by_group:
        raise NotFound(f"Commodity group not found: {group!r}")
    return list(store.commodities_by_group[group])


def _series_rows(store: Store, group: str, commodity: str) -> list[Row]:
    rows = store.series_by_key.get((group, commodity))
    if not rows:
        # Distinguish unknown-group vs unknown-commodity for a clearer message.
        if group not in store.commodities_by_group:
            raise NotFound(f"Commodity group not found: {group!r}")
        raise NotFound(f"Commodity not found in group {group!r}: {commodity!r}")
    return rows


def get_series(store: Store, group: str, commodity: str) -> list[SeriesRecord]:
    rows = _series_rows(store, group, commodity)
    return [
        SeriesRecord(
            season_year=r.season_year,
            msp=r.msp,
            season_price=r.season_price,
        )
        for r in rows
    ]


def get_insights(store: Store, group: str, commodity: str) -> Insights:
    rows = _series_rows(store, group, commodity)

    priced = [r for r in rows if r.season_price is not None]

    if priced:
        # Ties resolved by earliest season (rows are already sorted ascending).
        highest = max(priced, key=lambda r: (r.season_price, -_yr(r.season_year)))
        lowest = min(priced, key=lambda r: (r.season_price, _yr(r.season_year)))
        highest_season: Optional[str] = highest.season_year
        lowest_season: Optional[str] = lowest.season_year
    else:
        highest_season = None
        lowest_season = None

    # Latest = max season_year in the available series.
    latest = rows[-1]
    delta_abs: Optional[float] = None
    delta_pct: Optional[float] = None
    if latest.msp is not None and latest.season_price is not None:
        delta_abs = round(latest.season_price - latest.msp, 2)
        if latest.msp != 0:
            delta_pct = round((latest.season_price - latest.msp) / latest.msp * 100, 2)

    # Trend: compare latest priced vs previous priced.
    trend = "flat"
    if len(priced) >= 2:
        # priced preserves input order, which is ascending.
        latest_priced = priced[-1]
        prev_priced = priced[-2]
        if prev_priced.season_price and prev_priced.season_price != 0:
            change_pct = (
                (latest_priced.season_price - prev_priced.season_price)
                / prev_priced.season_price
                * 100
            )
            if change_pct > 1:
                trend = "up"
            elif change_pct < -1:
                trend = "down"

    return Insights(
        commodity_group=group,
        commodity=commodity,
        highest_season=highest_season,
        lowest_season=lowest_season,
        latest_delta_from_msp=delta_abs,
        latest_delta_percent=delta_pct,
        price_trend=trend,
    )


def _yr(season_year: str) -> int:
    return int(season_year.split("-", 1)[0])
