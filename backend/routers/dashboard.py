import re
import time

from fastapi import APIRouter, Request

from data.models import DashboardSummary
from routers.alerts import _build_alerts
from services.insight_calculator import compute_insights

router = APIRouter(prefix="/api")

_cache: dict | None = None
_cache_expires: float = 0.0
_TTL = 300  # 5 minutes


def _slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _commodity_slug(group: str, commodity: str) -> str:
    return f"{_slugify(group)}--{_slugify(commodity)}"


def _build_dashboard(store) -> dict:
    cards = []
    pulse_events = []

    for (group, commodity), records in store.series_by_key.items():
        ins = compute_insights(group, commodity, records)
        cards.append({
            "slug": _commodity_slug(group, commodity),
            "commodity": commodity,
            "group": group,
            "latestSeason": ins["latestSeason"],
            "latestReferencePrice": ins["latestReferencePrice"],
            "latestMsp": ins["latestMsp"],
            "latestDeltaPct": ins["latestDeltaPct"],
            "riskLevel": ins["riskLevel"],
            "seasonAvailability": ins["seasonAvailability"],
            "recommendationLabel": ins["recommendationLabel"],
            "priceTrend": ins["priceTrend"],
        })

        if ins["latestReferencePrice"] is not None and ins["latestMsp"] is not None:
            delta = ins["latestDeltaPct"]
            trend = ins["priceTrend"]
            pulse_events.append({
                "id": f"{group}-{commodity}",
                "commodity": commodity,
                "group": group,
                "season": ins["latestSeason"],
                "delta": delta,
                "deltaLabel": f"{'+' if delta >= 0 else ''}{delta * 100:.1f}%",
                "label": (
                    "firming vs MSP" if trend == "up"
                    else "softening vs MSP" if trend == "down"
                    else "steady vs MSP"
                ),
                "timeAgo": ins["latestSeason"],
            })

    cards.sort(key=lambda c: abs(c["latestDeltaPct"]), reverse=True)
    pulse_events.sort(key=lambda e: abs(e["delta"]), reverse=True)

    return {
        "dataMode": "seasonal_commodity",
        "totalCommodities": len(cards),
        "totalGroups": len(store.groups),
        "spotlight": cards[0] if cards else None,
        "movers": cards[:6],
        "alerts": _build_alerts(store)[:5],
        "pulseEvents": pulse_events[:6],
        "updatedAt": "Season sync active",
    }


@router.get("/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request) -> dict:
    global _cache, _cache_expires
    if _cache is not None and time.monotonic() < _cache_expires:
        return _cache
    _cache = _build_dashboard(request.app.state.store)
    _cache_expires = time.monotonic() + _TTL
    return _cache
