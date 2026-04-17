from fastapi import APIRouter, Query, Request

from backend.models.schemas import InsightsResponse
from backend.store import repository

router = APIRouter()


@router.get("/commodity-insights", response_model=InsightsResponse)
def commodity_insights(
    request: Request,
    group: str = Query(..., min_length=1),
    commodity: str = Query(..., min_length=1),
) -> InsightsResponse:
    store = request.app.state.store
    insights = repository.get_insights(store, group, commodity)
    return InsightsResponse(
        commodity_group=insights.commodity_group,
        commodity=insights.commodity,
        highest_season=insights.highest_season,
        lowest_season=insights.lowest_season,
        latest_delta_from_msp=insights.latest_delta_from_msp,
        latest_delta_percent=insights.latest_delta_percent,
        price_trend=insights.price_trend,
    )
