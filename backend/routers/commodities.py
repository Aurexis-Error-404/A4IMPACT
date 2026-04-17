from fastapi import APIRouter, Query, Request

from backend.models.schemas import CommoditiesResponse
from backend.store import repository

router = APIRouter()


@router.get("/commodities", response_model=CommoditiesResponse)
def commodities(
    request: Request,
    group: str = Query(..., min_length=1, description="Commodity group name"),
) -> CommoditiesResponse:
    store = request.app.state.store
    return CommoditiesResponse(
        commodity_group=group,
        commodities=repository.list_commodities(store, group),
    )
