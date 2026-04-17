from fastapi import APIRouter, HTTPException, Query, Request

from data.models import SeasonRecord

router = APIRouter(prefix="/api")


@router.get("/commodity-series", response_model=list[SeasonRecord])
async def get_series(
    request: Request,
    group: str = Query(...),
    commodity: str = Query(...),
) -> list[dict]:
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
    return store.series_by_key[key]
