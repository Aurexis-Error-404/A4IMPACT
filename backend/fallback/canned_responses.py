# Pre-computed CommodityInsightSummary responses for offline/demo mode.
# Generated from live API calls on 2026-04-17 using actual season data + Groq AI.
# Serve via GET /demo/canned/{commodity} — zero external calls.

CANNED: dict[str, dict] = {
    "Cotton": {
        "commodity": "Cotton",
        "group": "Fibre Crops",
        "latestSeason": "2025-26",
        "latestMsp": 7710.0,
        "latestReferencePrice": 6700.75,
        "latestDelta": -1009.25,
        "latestDeltaPct": -0.1309,
        "latestDeltaLabel": "Rs.1,009 below MSP (-13.1%)",
        "highestSeason": "2022-23",
        "highestPriceLabel": "Rs.7,256 in 2022-23",
        "priceTrend": "flat",
        "trendChangePct": 0.012,
        "seasonAvailability": "Kharif only",
        "kharifShare": 1.0,
        "rabiShare": 0.0,
        "riskLevel": "High",
        "recommendationLabel": "Lean sell",
        "confidenceLabel": "Moderate confidence",
        "recommendationRationale": (
            "Cotton prices have been consistently below MSP in recent seasons, "
            "with the latest price Rs.1,009 below MSP (-13.1%). "
            "The sustained floor proximity and flat trend suggest limited near-term recovery."
        ),
    },
    "Paddy(Common)": {
        "commodity": "Paddy(Common)",
        "group": "Cereals",
        "latestSeason": "2025-26",
        "latestMsp": 2369.0,
        "latestReferencePrice": 2436.03,
        "latestDelta": 67.03,
        "latestDeltaPct": 0.0283,
        "latestDeltaLabel": "Rs.67 above MSP (+2.8%)",
        "highestSeason": "2024-25",
        "highestPriceLabel": "Rs.2,459 in 2024-25",
        "priceTrend": "flat",
        "trendChangePct": -0.0093,
        "seasonAvailability": "Kharif only",
        "kharifShare": 1.0,
        "rabiShare": 0.0,
        "riskLevel": "Low",
        "recommendationLabel": "Hold",
        "confidenceLabel": "Moderate confidence",
        "recommendationRationale": (
            "Paddy price is Rs.67 above MSP (+2.8%) in 2025-26, providing a modest buffer. "
            "Trend is flat with slight softening from the 2024-25 peak of Rs.2,459. "
            "Hold is recommended while monitoring for further price direction."
        ),
    },
    "Groundnut": {
        "commodity": "Groundnut",
        "group": "Oil Seeds",
        "latestSeason": "2025-26",
        "latestMsp": 7263.0,
        "latestReferencePrice": 5066.59,
        "latestDelta": -2196.41,
        "latestDeltaPct": -0.3024,
        "latestDeltaLabel": "Rs.2,196 below MSP (-30.2%)",
        "highestSeason": "2022-23",
        "highestPriceLabel": "Rs.6,789 in 2022-23",
        "priceTrend": "flat",
        "trendChangePct": -0.0184,
        "seasonAvailability": "Kharif only",
        "kharifShare": 1.0,
        "rabiShare": 0.0,
        "riskLevel": "High",
        "recommendationLabel": "Lean sell",
        "confidenceLabel": "Low confidence",
        "recommendationRationale": (
            "Groundnut prices are significantly below MSP at -30.2%, a persistent pattern across seasons. "
            "The latest Kharif price of Rs.5,067 is Rs.2,196 below MSP with no clear recovery signal. "
            "Consider staged selling to limit exposure to further downside."
        ),
    },
}
