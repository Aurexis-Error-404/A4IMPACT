from fastapi import APIRouter, HTTPException, Path

from data.models import CommodityInsightSummary
from fallback.canned_responses import CANNED

router = APIRouter(prefix="/demo")


@router.get("/canned/{commodity}", response_model=CommodityInsightSummary)
async def get_canned(commodity: str = Path(...)) -> dict:
    if commodity not in CANNED:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "no_canned_response",
                "commodity": commodity,
                "available": list(CANNED.keys()),
            },
        )
    return CANNED[commodity]
