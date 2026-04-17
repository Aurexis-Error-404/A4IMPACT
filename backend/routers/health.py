from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    store = request.app.state.store
    commodity_count = sum(len(cs) for cs in store.commodities_by_group.values())
    return {
        "status": "ok",
        "data_mode": "seasonal_commodity",
        "commodities": commodity_count,
        "records": len(store.records),
        "groups": store.groups,
    }
