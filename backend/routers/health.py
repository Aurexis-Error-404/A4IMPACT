from fastapi import APIRouter, Request

from backend.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    store = request.app.state.store
    total_commodities = sum(len(v) for v in store.commodities_by_group.values())
    return HealthResponse(
        rows_loaded=len(store.rows),
        groups=len(store.groups),
        commodities=total_commodities,
    )
