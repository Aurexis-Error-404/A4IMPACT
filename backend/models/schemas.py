from typing import Literal, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data_mode: Literal["seasonal_commodity"] = "seasonal_commodity"
    rows_loaded: int
    groups: int
    commodities: int


class GroupsResponse(BaseModel):
    groups: list[str]


class CommoditiesResponse(BaseModel):
    commodity_group: str
    commodities: list[str]


class SeriesRecord(BaseModel):
    season_year: str
    msp: Optional[int] = None
    season_price: Optional[float] = None


class SeriesResponse(BaseModel):
    commodity_group: str
    commodity: str
    records: list[SeriesRecord]


class InsightsResponse(BaseModel):
    commodity_group: str
    commodity: str
    highest_season: Optional[str] = None
    lowest_season: Optional[str] = None
    latest_delta_from_msp: Optional[float] = None
    latest_delta_percent: Optional[float] = None
    price_trend: Literal["up", "down", "flat"] = "flat"


class ErrorDetail(BaseModel):
    code: Literal["MISSING_PARAM", "NOT_FOUND", "INVALID_INPUT", "SERVER_ERROR"]
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail
