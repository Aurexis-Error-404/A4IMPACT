from fastapi import APIRouter, HTTPException, Path, Request

from data.models import ProfitEstimateRequest, ProfitEstimateResponse
from services.insight_calculator import compute_insights, get_expected_price_range
from services.pre_analysis_enricher import enrich
from services.staging import compute_staging

router = APIRouter(prefix="/api")


def _find(store, commodity: str) -> tuple[str, str] | None:
    for g, c in store.series_by_key:
        if c == commodity:
            return g, c
    return None


def _profit(price: float | None, cost: float | None, qty: float) -> float | None:
    if price is None:
        return None
    if cost is None:
        return round(price * qty, 2)
    return round((price - cost) * qty, 2)


@router.post("/profit-estimate/{commodity}", response_model=ProfitEstimateResponse)
async def profit_estimate(
    request: Request,
    body: ProfitEstimateRequest,
    commodity: str = Path(...),
) -> ProfitEstimateResponse:
    store = request.app.state.store

    match = _find(store, commodity)
    if not match:
        raise HTTPException(
            status_code=404,
            detail={"error": "commodity_not_found", "commodity": commodity},
        )

    group, comm = match
    records  = store.series_by_key[(group, comm)]
    insight  = compute_insights(group, comm, records)
    enriched = enrich(records)

    qty  = body.quantity_quintals
    cost = body.cost_per_quintal

    current_price = insight.get("latestReferencePrice")
    msp_price     = insight.get("latestMsp")
    price_range   = get_expected_price_range(records)
    ceiling_price = price_range.ceiling if price_range else None

    sell_pct, hold_pct = compute_staging(
        insight["riskLevel"],
        insight["priceTrend"],
        insight["confidenceLabel"],
    )

    staging_advice = (
        f"Sell {sell_pct}% now"
        + (f" at ~Rs.{current_price:,.0f}/quintal" if current_price else "")
        + f", hold {hold_pct}%"
        + (f" for potential ceiling of Rs.{ceiling_price:,.0f}/quintal" if ceiling_price else "")
        + "."
    )

    return ProfitEstimateResponse(
        commodity=comm,
        quantity_quintals=qty,
        cost_per_quintal=cost,
        profit_at_msp=_profit(msp_price, cost, qty),
        profit_at_current=_profit(current_price, cost, qty),
        profit_at_ceiling=_profit(ceiling_price, cost, qty),
        breakeven_price=cost,
        expected_range=price_range,
        sell_pct_now=sell_pct,
        hold_pct=hold_pct,
        staging_advice=staging_advice,
    )
