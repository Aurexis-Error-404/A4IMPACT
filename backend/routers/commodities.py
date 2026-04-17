from fastapi import APIRouter, HTTPException, Query, Request

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
