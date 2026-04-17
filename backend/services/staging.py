def compute_staging(risk_level: str, trend: str, confidence_label: str) -> tuple[int, int]:
    """
    Deterministic sell/hold percentage split.
    Confidence now affects all risk tiers — high confidence = more decisive split.
    Returns (sell_pct_now, hold_pct); always sums to 100.
    """
    high_conf = confidence_label == "High confidence"

    if risk_level == "High" and trend == "down":
        return (80, 20) if high_conf else (70, 30)
    if risk_level == "High":
        return (50, 50) if high_conf else (40, 60)
    if risk_level == "Watch" and trend == "down":
        return (60, 40) if high_conf else (50, 50)
    if risk_level == "Watch":
        return (35, 65) if high_conf else (30, 70)
    # Low risk
    if trend == "up" and high_conf:
        return 10, 90
    if trend == "up":
        return 20, 80
    return 20, 80
