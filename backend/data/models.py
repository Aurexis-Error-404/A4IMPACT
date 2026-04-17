from typing import Literal
from pydantic import BaseModel

SeasonAvailability = Literal["Kharif only", "Rabi only", "Both", "Sparse"]
RiskLevel = Literal["Low", "Watch", "High"]
TrendDirection = Literal["up", "down", "flat"]
RecommendationLabel = Literal["Hold", "Lean sell", "Defer", "Protect"]
ConfidenceLabel = Literal["High confidence", "Moderate confidence", "Low confidence"]


class SeasonRecord(BaseModel):
    season_year: str
    commodity_group: str
    commodity: str
    msp: float | None = None
    kharif_price: float | None = None
    kharif_arrival_tonnes: float | None = None
    rabi_price: float | None = None
    rabi_arrival_tonnes: float | None = None
    source_file: str = ""


class CommodityInsightSummary(BaseModel):
    commodity: str
    group: str
    latestSeason: str
    latestMsp: float | None
    latestReferencePrice: float | None
    latestDelta: float
    latestDeltaPct: float           # decimal: 0.12 = 12%
    latestDeltaLabel: str
    highestSeason: str
    highestPriceLabel: str
    priceTrend: TrendDirection
    trendChangePct: float
    seasonAvailability: SeasonAvailability
    kharifShare: float
    rabiShare: float
    riskLevel: RiskLevel
    recommendationLabel: RecommendationLabel
    confidenceLabel: ConfidenceLabel
    recommendationRationale: str
