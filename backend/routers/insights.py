from fastapi import APIRouter, HTTPException, Query, Request

from data.models import CommodityInsightSummary
from services.insight_calculator import compute_insights

router = APIRouter(prefix="/api")


@router.get("/commodity-insights", response_model=CommodityInsightSummary)
async def get_insights(
    request: Request,
    group: str = Query(...),
    commodity: str = Query(...),
) -> dict:
    store = request.app.state.store
    key = (group, commodity)
    if key not in store.series_by_key:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "commodity_not_found",
                "group": group,
                "commodity": commodity,
            },
        )
    return compute_insights(group, commodity, store.series_by_key[key])
