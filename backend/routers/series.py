from fastapi import APIRouter, Query, Request

from backend.models.schemas import SeriesRecord, SeriesResponse
from backend.store import repository

router = APIRouter()


@router.get("/commodity-series", response_model=SeriesResponse)
def commodity_series(
    request: Request,
    group: str = Query(..., min_length=1),
    commodity: str = Query(..., min_length=1),
) -> SeriesResponse:
    store = request.app.state.store
    rows = repository.get_series(store, group, commodity)
    return SeriesResponse(
        commodity_group=group,
        commodity=commodity,
        records=[
            SeriesRecord(
                season_year=r.season_year,
                msp=r.msp,
                season_price=r.season_price,
            )
            for r in rows
        ],
    )
