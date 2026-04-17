from typing import Literal
from pydantic import BaseModel



SeasonAvailability = Literal["Kharif only", "Rabi only", "Both", "Sparse"]
RiskLevel = Literal["Low", "Watch", "High"]
TrendDirection = Literal["up", "down", "flat"]
RecommendationLabel = Literal["Hold", "Lean sell", "Defer", "Protect"]
ConfidenceLabel = Literal["High confidence", "Moderate confidence", "Low confidence"]


class PriceRange(BaseModel):
    floor: float
    ceiling: float
    basis: str


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


class AlertItem(BaseModel):
    id: str
    severity: Literal["red", "amber", "green"]
    commodity: str
    group: str
    headline: str
    detail: str
    season: str


class ProfitEstimateRequest(BaseModel):
    quantity_quintals: float
    cost_per_quintal: float | None = None


class ProfitEstimateResponse(BaseModel):
    commodity: str
    quantity_quintals: float
    cost_per_quintal: float | None
    profit_at_msp: float | None
    profit_at_current: float | None
    profit_at_ceiling: float | None
    breakeven_price: float | None
    expected_range: PriceRange | None
    sell_pct_now: int
    hold_pct: int
    staging_advice: str


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
    # Extended intelligence fields — all optional so cached responses stay valid
    deltaPctHistory: list[float] = []
    expectedPriceRange: PriceRange | None = None
    recommendedChannel: str = ""
    sellPctNow: int = 0
    holdPct: int = 100
    actionableTiming: str = ""
    conflictScore: str = "LOW"


class CommodityPair(BaseModel):
    group: str
    commodity: str


class CommodityCardSummary(BaseModel):
    slug: str
    commodity: str
    group: str
    latestSeason: str
    latestReferencePrice: float | None
    latestMsp: float | None
    latestDeltaPct: float
    riskLevel: RiskLevel
    seasonAvailability: SeasonAvailability
    recommendationLabel: RecommendationLabel
    priceTrend: TrendDirection


class PulseEvent(BaseModel):
    id: str
    commodity: str
    group: str
    season: str
    deltaLabel: str
    delta: float
    label: str
    timeAgo: str


class DashboardSummary(BaseModel):
    dataMode: str
    totalCommodities: int
    totalGroups: int
    spotlight: CommodityCardSummary | None
    movers: list[CommodityCardSummary]
    alerts: list[AlertItem]
    pulseEvents: list[PulseEvent]
    updatedAt: str
