def compute_staging(risk_level: str, trend: str, confidence_label: str) -> tuple[int, int]:
    """
    Deterministic sell/hold percentage split based on merged risk signals.
    Returns (sell_pct_now, hold_pct); always sums to 100.
    """
    if risk_level == "High" and trend == "down":
        return 70, 30
    if risk_level == "High":
        return 40, 60
    if risk_level == "Watch" and trend == "down":
        return 50, 50
    if risk_level == "Watch":
        return 30, 70
    # Low risk
    if trend == "up" and confidence_label == "High confidence":
        return 10, 90
    if trend == "up":
        return 20, 80
    return 20, 80
