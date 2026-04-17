from __future__ import annotations
from statistics import mean, stdev


def _ref_price(r: dict) -> float | None:
    return r.get("kharif_price") or r.get("rabi_price")


def _total_arrivals(r: dict) -> float:
    return (r.get("kharif_arrival_tonnes") or 0.0) + (r.get("rabi_arrival_tonnes") or 0.0)


def enrich(records: list[dict]) -> dict:
    """
    Pure function. Derives analytics signals from sorted season records (oldest → latest).
    Returns a flat dict injected into agent prompts and insight calculations.
    Never modifies records or reads from disk.
    """
    if not records:
        return {
            "data_confidence": "Low",
            "anomaly_flags": [],
            "anomaly_seasons": [],
            "msp_cagr": None,
            "price_cagr": None,
            "msp_price_divergence": "stable",
            "arrival_velocity": None,
            "arrival_collapse_pct": None,
            "floor_proximity_trend": "stable",
        }

    priced = [r for r in records if _ref_price(r) is not None]

    # ── Anomaly detection ────────────────────────────────────────────────────
    # Flag any season where a reported price is < 50% of MSP — likely data error.
    anomaly_flags: list[str] = []
    anomaly_seasons: list[str] = []
    for r in records:
        kp = r.get("kharif_price")
        rp = r.get("rabi_price")
        msp = r.get("msp")
        if not msp or msp <= 0:
            continue
        if kp is not None and kp < 0.5 * msp:
            anomaly_flags.append(
                f"{r['season_year']} Kharif Rs.{kp:,.0f} < 50% of MSP Rs.{msp:,.0f} — suspect"
            )
            if r["season_year"] not in anomaly_seasons:
                anomaly_seasons.append(r["season_year"])
        if rp is not None and rp < 0.5 * msp:
            anomaly_flags.append(
                f"{r['season_year']} Rabi Rs.{rp:,.0f} < 50% of MSP Rs.{msp:,.0f} — suspect"
            )
            if r["season_year"] not in anomaly_seasons:
                anomaly_seasons.append(r["season_year"])

    # ── Data confidence ──────────────────────────────────────────────────────
    if len(priced) < 2:
        data_confidence = "Low"
    elif len(priced) < 3 or anomaly_flags:
        data_confidence = "Moderate"
    else:
        data_confidence = "High"

    # ── CAGR calculations ────────────────────────────────────────────────────
    msp_cagr: float | None = None
    price_cagr: float | None = None

    msp_vals = [r.get("msp") for r in records if r.get("msp")]
    price_vals = [p for p in (_ref_price(r) for r in records) if p is not None]

    if len(msp_vals) >= 2:
        m0, m1 = msp_vals[0], msp_vals[-1]
        n = len(msp_vals) - 1
        if m0 > 0:
            msp_cagr = round((m1 / m0) ** (1.0 / n) - 1, 4)

    if len(price_vals) >= 2:
        p0, p1 = price_vals[0], price_vals[-1]
        n = len(price_vals) - 1
        if p0 > 0:
            price_cagr = round((p1 / p0) ** (1.0 / n) - 1, 4)

    # ── MSP-vs-price divergence ──────────────────────────────────────────────
    # Positive divergence = price pulling above MSP; negative = falling further below.
    msp_price_divergence = "stable"
    if len(priced) >= 2:
        r0, r1 = priced[0], priced[-1]
        m0, m1 = r0.get("msp"), r1.get("msp")
        p0, p1 = _ref_price(r0), _ref_price(r1)
        if m0 and m1 and p0 is not None and p1 is not None and m0 > 0 and m1 > 0:
            gap_early = (p0 - m0) / m0
            gap_late = (p1 - m1) / m1
            delta = gap_late - gap_early
            if delta > 0.05:
                msp_price_divergence = "widening_positive"
            elif delta < -0.05:
                msp_price_divergence = "widening_negative"

    # ── Arrival analytics ────────────────────────────────────────────────────
    arrival_series = [_total_arrivals(r) for r in records]
    arrival_velocity: float | None = None
    arrival_collapse_pct: float | None = None

    nonzero = [a for a in arrival_series if a > 0]
    if len(nonzero) >= 2 and len(records) > 1:
        arrival_velocity = round(
            (arrival_series[-1] - arrival_series[0]) / (len(records) - 1), 2
        )
        peak = max(nonzero)
        latest = arrival_series[-1]
        if peak > 0:
            arrival_collapse_pct = round((peak - latest) / peak * 100, 1)

    # ── Floor proximity trend ────────────────────────────────────────────────
    # Are prices converging toward MSP (approaching_floor) or pulling away?
    floor_proximity_trend = "stable"
    if len(priced) >= 2:
        r0, r1 = priced[0], priced[-1]
        m0, m1 = r0.get("msp"), r1.get("msp")
        p0, p1 = _ref_price(r0), _ref_price(r1)
        if m0 and m1 and p0 is not None and p1 is not None and m0 > 0 and m1 > 0:
            pct0 = (p0 - m0) / m0
            pct1 = (p1 - m1) / m1
            diff = pct1 - pct0
            if diff < -0.05:
                floor_proximity_trend = "approaching_floor"
            elif diff > 0.05:
                floor_proximity_trend = "moving_away_from_floor"

    # ── MSP hit rate ─────────────────────────────────────────────────────────
    # Fraction of priced seasons where reference price >= MSP.
    above_msp = sum(
        1 for r in priced
        if r.get("msp") and _ref_price(r) is not None and _ref_price(r) >= r["msp"]  # type: ignore[operator]
    )
    msp_hit_rate = round(above_msp / len(priced), 3) if priced else 0.0

    # ── Price volatility ──────────────────────────────────────────────────────
    # Std dev of (price/MSP - 1) — high value means unreliable price swings.
    vol_deltas = [
        (_ref_price(r) / r["msp"]) - 1  # type: ignore[operator]
        for r in priced if r.get("msp") and r["msp"] > 0 and _ref_price(r) is not None
    ]
    price_volatility = round(stdev(vol_deltas), 4) if len(vol_deltas) >= 2 else 0.0

    # ── Recent momentum ───────────────────────────────────────────────────────
    # Compare avg (price/MSP - 1) of last 2 seasons vs all prior seasons.
    recent_momentum = "stable"
    if len(priced) >= 3:
        def _dm(r: dict) -> float:
            p, m = _ref_price(r), r.get("msp")
            return (p / m) - 1 if p is not None and m and m > 0 else 0.0  # type: ignore[operator]

        recent_avg = mean(_dm(r) for r in priced[-2:])
        prior_avg  = mean(_dm(r) for r in priced[:-2])
        diff = recent_avg - prior_avg
        recent_momentum = "improving" if diff > 0.03 else "declining" if diff < -0.03 else "stable"

    return {
        "data_confidence": data_confidence,
        "anomaly_flags": anomaly_flags,
        "anomaly_seasons": anomaly_seasons,
        "msp_cagr": msp_cagr,
        "price_cagr": price_cagr,
        "msp_price_divergence": msp_price_divergence,
        "arrival_velocity": arrival_velocity,
        "arrival_collapse_pct": arrival_collapse_pct,
        "floor_proximity_trend": floor_proximity_trend,
        "msp_hit_rate": msp_hit_rate,
        "price_volatility": price_volatility,
        "recent_momentum": recent_momentum,
    }
