from fastapi import APIRouter, HTTPException, Query, Request

from data.models import CommodityPair

router = APIRouter(prefix="/api")


@router.get("/commodity-groups")
async def list_groups(request: Request) -> list[str]:
    return request.app.state.store.groups


@router.get("/commodities")
async def list_commodities(
    request: Request,
    group: str = Query(..., description="Commodity group name"),
) -> list[str]:
    store = request.app.state.store
    if group not in store.commodities_by_group:
        raise HTTPException(
            status_code=404,
            detail={"error": "group_not_found", "group": group, "available": store.groups},
        )
    return store.commodities_by_group[group]


@router.get("/commodity-pairs", response_model=list[CommodityPair])
async def list_pairs(request: Request) -> list[dict]:
    """All (group, commodity) pairs in one request — replaces the 1+N group fetch fan-out."""
    store = request.app.state.store
    return [
        {"group": group, "commodity": commodity}
        for group in store.groups
        for commodity in store.commodities_by_group.get(group, [])
    ]
