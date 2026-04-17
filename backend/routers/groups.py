from fastapi import APIRouter, Request

from backend.models.schemas import GroupsResponse
from backend.store import repository

router = APIRouter()


@router.get("/commodity-groups", response_model=GroupsResponse)
def commodity_groups(request: Request) -> GroupsResponse:
    store = request.app.state.store
    return GroupsResponse(groups=repository.list_groups(store))
