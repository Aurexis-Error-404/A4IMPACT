from __future__ import annotations

from data.models import (
    SeasonAvailability,
    RiskLevel,
    TrendDirection,
    RecommendationLabel,
    PriceRange,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ref_price(r: dict) -> float | None:
    """Prefer Kharif price; fall back to Rabi."""
    return r.get("kharif_price") or r.get("rabi_price")


def _priced(records: list[dict]) -> list[dict]:
    return [r for r in records if _ref_price(r) is not None]


# ---------------------------------------------------------------------------
# Public pure functions
# ---------------------------------------------------------------------------

def get_season_availability(records: list[dict]) -> SeasonAvailability:
    has_k = any(r.get("kharif_price") is not None for r in records)
    has_r = any(r.get("rabi_price") is not None for r in records)
    if has_k and has_r:
        return "Both"
    if has_k:
        return "Kharif only"
    if has_r:
        return "Rabi only"
    return "Sparse"


def get_kharif_rabi_shares(records: list[dict]) -> tuple[float, float]:
    total_k = sum(r.get("kharif_arrival_tonnes") or 0.0 for r in records)
    total_r = sum(r.get("rabi_arrival_tonnes") or 0.0 for r in records)
    total = total_k + total_r
    if total == 0:
        return 0.0, 0.0
    return round(total_k / total, 4), round(total_r / total, 4)


def get_price_trend(records: list[dict]) -> tuple[TrendDirection, float]:
    priced = _priced(records)
    if len(priced) < 2:
        return "flat", 0.0
    prev = _ref_price(priced[-2])
    curr = _ref_price(priced[-1])
    if prev is None or curr is None or prev == 0:
        return "flat", 0.0
    change = (curr - prev) / prev
    if change > 0.02:
        return "up", round(change, 4)
    if change < -0.02:
        return "down", round(change, 4)
    return "flat", round(change, 4)


def get_highest_season(records: list[dict]) -> tuple[str, float | None]:
    priced = _priced(records)
    if not priced:
        return "", None
    best = max(priced, key=lambda r: _ref_price(r))  # type: ignore[arg-type]
    return best["season_year"], _ref_price(best)


def get_lowest_season(records: list[dict]) -> tuple[str, float | None]:
    priced = _priced(records)
    if not priced:
        return "", None
    worst = min(priced, key=lambda r: _ref_price(r))  # type: ignore[arg-type]
    return worst["season_year"], _ref_price(worst)


def get_delta_pct_history(records: list[dict]) -> list[float]:
    result = []
    for r in records:
        price = _ref_price(r)
        msp = r.get("msp")
        if price is not None and msp and msp > 0:
            result.append(round((price - msp) / msp, 4))
        else:
            result.append(0.0)
    return result


def get_expected_price_range(records: list[dict]) -> PriceRange | None:
    priced = _priced(records)
    if not priced:
        return None
    prices = [_ref_price(r) for r in priced]  # all non-None by construction
    msps = [r.get("msp") for r in priced if r.get("msp")]
    raw_floor = min(prices)  # type: ignore[type-var]
    ceiling = max(prices)    # type: ignore[type-var]
    # Effective floor = observed minimum but never below the lowest MSP
    msp_floor = min(msps) if msps else None
    effective_floor = max(raw_floor, msp_floor) if msp_floor else raw_floor
    return PriceRange(
        floor=round(effective_floor, 2),
        ceiling=round(ceiling, 2),
        basis=f"{len(priced)}-season observed range",
    )


def get_recommended_channel(delta_pct: float, availability: SeasonAvailability) -> str:
    if availability == "Sparse":
        return "Contact local APMC for current rates"
    if delta_pct < -0.05:
        return "Government Procurement (FCI/NAFED) — price below MSP, MSP protection applies"
    if delta_pct > 0.10:
        return "Open Market (APMC) — price well above MSP, competitive rates favourable"
    return "Either (APMC or FCI) — price near MSP, compare local rates before selling"


def get_risk_level(delta_pct: float, availability: SeasonAvailability) -> RiskLevel:
    if availability == "Sparse":
        return "High"
    if delta_pct < -0.15:
        return "High"
    if delta_pct < -0.05:
        return "Watch"
    return "Low"


def get_recommendation(
    risk: RiskLevel,
    trend: TrendDirection,
) -> tuple[RecommendationLabel, str]:
    if risk == "High" and trend == "down":
        return (
            "Protect",
            "Price is significantly below MSP and declining. "
            "Consider government procurement channels or minimum-loss exit.",
        )
    if risk == "High":
        return (
            "Defer",
            "Price is well below MSP. Defer sale if storage allows; "
            "monitor for recovery before committing.",
        )
    if risk == "Watch" and trend == "down":
        return (
            "Lean sell",
            "Price is below MSP and trending downward. "
            "Selling now may limit further losses.",
        )
    if risk == "Low" and trend == "up":
        return (
            "Hold",
            "Price is above MSP and rising. "
            "Holding may yield better returns this season.",
        )
    return (
        "Hold",
        "Price is near or above MSP with no strong directional signal. "
        "Standard sell timeline applies.",
    )


# ---------------------------------------------------------------------------
# Aggregate builder
# ---------------------------------------------------------------------------

def compute_insights(group: str, commodity: str, records: list[dict]) -> dict:
    """Build a full CommodityInsightSummary dict from sorted season records."""
    if not records:
        raise ValueError(f"No records found for {group} / {commodity}")

    latest = records[-1]
    latest_price = _ref_price(latest)
    latest_msp: float | None = latest.get("msp")

    # Delta from MSP
    if latest_price is not None and latest_msp:
        delta = round(latest_price - latest_msp, 2)
        delta_pct = round(delta / latest_msp, 4)
    else:
        delta = 0.0
        delta_pct = 0.0

    # Human-readable delta label
    if delta > 0:
        delta_label = f"Rs.{delta:,.0f} above MSP ({delta_pct * 100:+.1f}%)"
    elif delta < 0:
        delta_label = f"Rs.{abs(delta):,.0f} below MSP ({delta_pct * 100:+.1f}%)"
    else:
        delta_label = "At MSP"

    trend, trend_change_pct = get_price_trend(records)
    highest_season, highest_price = get_highest_season(records)
    lowest_season, _ = get_lowest_season(records)
    availability = get_season_availability(records)
    kharif_share, rabi_share = get_kharif_rabi_shares(records)
    risk = get_risk_level(delta_pct, availability)
    rec_label, rationale = get_recommendation(risk, trend)

    highest_label = (
        f"Rs.{highest_price:,.0f} in {highest_season}" if highest_price else ""
    )

    # Sparse data → always Low confidence regardless of other signals
    priced_count = len([r for r in records if _ref_price(r) is not None])
    confidence: str = "Low confidence" if priced_count < 3 else "Moderate confidence"

    delta_pct_history = get_delta_pct_history(records)
    expected_price_range = get_expected_price_range(records)
    recommended_channel = get_recommended_channel(delta_pct, availability)

    return {
        "commodity": commodity,
        "group": group,
        "latestSeason": latest["season_year"],
        "latestMsp": latest_msp,
        "latestReferencePrice": latest_price,
        "latestDelta": delta,
        "latestDeltaPct": delta_pct,
        "latestDeltaLabel": delta_label,
        "highestSeason": highest_season,
        "highestPriceLabel": highest_label,
        "priceTrend": trend,
        "trendChangePct": trend_change_pct,
        "seasonAvailability": availability,
        "kharifShare": kharif_share,
        "rabiShare": rabi_share,
        "riskLevel": risk,
        "recommendationLabel": rec_label,
        "confidenceLabel": confidence,
        "recommendationRationale": rationale,
        "deltaPctHistory": delta_pct_history,
        "expectedPriceRange": expected_price_range,
        "recommendedChannel": recommended_channel,
    }
