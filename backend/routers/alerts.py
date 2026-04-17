import time

from fastapi import APIRouter, Request

from data.models import AlertItem
from services.insight_calculator import compute_insights
from services.pre_analysis_enricher import enrich

router = APIRouter(prefix="/api")

_cache: dict | None = None
_cache_expires: float = 0.0
_TTL = 3600  # 1 hour


def _build_alerts(store) -> list[dict]:
    alerts: list[dict] = []
    for (group, commodity), records in store.series_by_key.items():
        insight  = compute_insights(group, commodity, records)
        enriched = enrich(records)
        risk     = insight["riskLevel"]

        # Downgrade red → amber when data confidence is Low (unreliable signal)
        if risk == "High" and enriched["data_confidence"] == "Low":
            risk = "Watch"

        if risk not in ("High", "Watch"):
            continue

        severity  = "red" if risk == "High" else "amber"
        delta_pct = insight["latestDeltaPct"]
        latest_price = insight["latestReferencePrice"]
        msp      = insight["latestMsp"]
        season   = insight["latestSeason"]
        rec      = insight["recommendationLabel"]

        if delta_pct < 0:
            headline = f"{commodity} {abs(delta_pct) * 100:.1f}% below MSP — {rec} recommended"
            detail   = (
                f"Kharif price Rs.{latest_price:,.0f} vs MSP Rs.{msp:,.0f} in {season}"
                if latest_price and msp else insight["latestDeltaLabel"]
            )
        else:
            headline = f"{commodity} within 5% of MSP — consider partial sell to lock in gains"
            detail   = f"Price Rs.{latest_price:,.0f} vs MSP Rs.{msp:,.0f} in {season} — watch for reversal"

        # Append anomaly context when present
        if enriched["anomaly_flags"]:
            detail += " — ⚠ suspect data"

        # Append arrival collapse context when significant
        collapse = enriched.get("arrival_collapse_pct")
        if collapse is not None and collapse > 50:
            detail += f" | Arrival volume down {collapse:.0f}% from peak"

        slug = commodity.lower().replace("(", "").replace(")", "").replace(" ", "-")
        alerts.append(
            AlertItem(
                id=f"{slug}-{season}",
                severity=severity,
                commodity=commodity,
                group=group,
                headline=headline,
                detail=detail,
                season=season,
            ).model_dump()
        )

    alerts.sort(key=lambda a: (0 if a["severity"] == "red" else 1, a["commodity"]))
    return alerts


@router.get("/alerts", response_model=list[AlertItem])
async def get_alerts(request: Request) -> list[dict]:
    global _cache, _cache_expires
    if _cache is not None and time.monotonic() < _cache_expires:
        return _cache

    store = request.app.state.store
    _cache = _build_alerts(store)
    _cache_expires = time.monotonic() + _TTL
    return _cache
