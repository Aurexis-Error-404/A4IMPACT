import asyncio
import logging

from fastapi import APIRouter, HTTPException, Path, Request

logger = logging.getLogger(__name__)

from agents import mediator, risk_analyst, season_optimist, season_pessimist
from data.models import CommodityInsightSummary
from services.insight_calculator import compute_insights
from services import recommendation_cache
from services.pre_analysis_enricher import enrich
from services.staging import compute_staging

router = APIRouter(prefix="/api")

_VALID_REC  = {"Hold", "Lean sell", "Defer", "Protect"}
_VALID_CONF = {"High confidence", "Moderate confidence", "Low confidence"}
_VALID_RISK = {"Low", "Watch", "High"}

# Normalise common LLM capitalisation/formatting variants before set-membership check.
# Keys are lowercased stripped strings; values are the exact TypeScript literal.
_LABEL_MAP: dict[str, str] = {
    # recommendationLabel
    "hold":       "Hold",
    "lean sell":  "Lean sell",
    "lean_sell":  "Lean sell",
    "leansell":   "Lean sell",
    "defer":      "Defer",
    "protect":    "Protect",
    # confidenceLabel
    "high confidence":     "High confidence",
    "high_confidence":     "High confidence",
    "moderate confidence": "Moderate confidence",
    "moderate_confidence": "Moderate confidence",
    "low confidence":      "Low confidence",
    "low_confidence":      "Low confidence",
    # riskLevel
    "low":   "Low",
    "watch": "Watch",
    "high":  "High",
}


def _find(store, commodity: str) -> tuple[str, str] | None:
    for g, c in store.series_by_key:
        if c == commodity:
            return g, c
    return None


def _normalise(raw: str) -> str:
    """Map raw LLM string to canonical literal, or return raw unchanged."""
    return _LABEL_MAP.get(raw.strip().lower(), raw) if isinstance(raw, str) else raw


def _aggregate_verdicts(opt: dict, pess: dict, risk: dict) -> dict:
    """Rule-based fallback when mediator or agents fail."""
    verdicts   = [opt.get("verdict", ""), pess.get("verdict", ""), risk.get("verdict", "")]
    risk_level = risk.get("risk_level", "Watch")
    if risk_level not in _VALID_RISK:
        risk_level = "Watch"

    counts = {v: verdicts.count(v) for v in ("PROTECT", "DEFER", "LEAN_SELL", "HOLD")}
    if counts["PROTECT"] >= 2:
        label = "Protect"
    elif counts["DEFER"] >= 2:
        label = "Defer"
    elif counts["LEAN_SELL"] >= 2:
        label = "Lean sell"
    else:
        label = "Hold"

    return {
        "recommendationLabel": label,
        "confidenceLabel": "Low confidence",
        "riskLevel": risk_level,
        "recommendationRationale": (
            "Rule-based assessment: agents provided mixed or unavailable signals. "
            "Review data manually before acting."
        ),
        "conflict_score": "HIGH",
    }


def _sanitize(med: dict, base: dict) -> dict:
    """Ensure mediator output matches TypeScript union literals exactly."""
    rec      = _normalise(med.get("recommendationLabel", ""))
    conf     = _normalise(med.get("confidenceLabel", ""))
    risk     = _normalise(med.get("riskLevel", ""))
    rationale = med.get("recommendationRationale", "")
    timing   = med.get("actionable_timing", "")
    conflict = med.get("conflict_score", "LOW")

    return {
        "recommendationLabel":   rec  if rec  in _VALID_REC  else base["recommendationLabel"],
        "confidenceLabel":       conf if conf in _VALID_CONF else "Moderate confidence",
        "riskLevel":             risk if risk in _VALID_RISK else base["riskLevel"],
        "recommendationRationale": rationale if isinstance(rationale, str) and rationale
                                               else base["recommendationRationale"],
        "actionableTiming": timing if isinstance(timing, str) else "",
        "conflictScore":    conflict if conflict in {"LOW", "MEDIUM", "HIGH"} else "LOW",
    }



@router.post("/recommendation/{commodity}", response_model=CommodityInsightSummary)
async def get_recommendation(
    request: Request,
    commodity: str = Path(...),
) -> dict:
    store = request.app.state.store

    cached = recommendation_cache.get(commodity)
    if cached:
        return cached

    match = _find(store, commodity)
    if not match:
        raise HTTPException(
            status_code=404,
            detail={"error": "commodity_not_found", "commodity": commodity},
        )
    group, comm = match
    records = store.series_by_key[(group, comm)]

    # Deterministic base (always succeeds)
    base = compute_insights(group, comm, records)

    # Pre-compute enriched analytics once; passed into every agent prompt
    enriched = enrich(records)

    # 3 agents in parallel — 2 s stagger to spread Groq TPM load
    # Pre-initialize so the outer except block can safely reference them
    opt, pess, risk = {}, {}, {}
    ai_ran = False
    try:
        logger.info("recommendation/%s: spawning 3 Groq agents", comm)
        results = await asyncio.gather(
            season_optimist.analyze(comm, group, records, delay=0,  enriched=enriched),
            season_pessimist.analyze(comm, group, records, delay=2, enriched=enriched),
            risk_analyst.analyze(comm, group, records, delay=4,     enriched=enriched),
            return_exceptions=True,
        )

        def _unwrap(tag: str, res):
            if isinstance(res, dict):
                logger.info("recommendation/%s: %s agent OK (verdict=%s)", comm, tag, res.get("verdict"))
                return res
            logger.warning("recommendation/%s: %s agent FAILED — %s", comm, tag, res)
            return {}

        opt  = _unwrap("optimist",  results[0])
        pess = _unwrap("pessimist", results[1])
        risk = _unwrap("risk",      results[2])

        if any([opt, pess, risk]):
            try:
                logger.info("recommendation/%s: calling mediator", comm)
                med_raw = await mediator.synthesize(comm, opt, pess, risk, base, enriched=enriched)
                med = _sanitize(med_raw, base)
                ai_ran = True
                logger.info("recommendation/%s: mediator OK (label=%s, confidence=%s, conflict=%s)",
                            comm, med.get("recommendationLabel"), med.get("confidenceLabel"), med.get("conflictScore"))
            except Exception as exc:
                logger.warning("recommendation/%s: mediator FAILED — %s; falling back to rule-based", comm, exc)
                med = _aggregate_verdicts(opt, pess, risk)
        else:
            logger.warning("recommendation/%s: ALL agents failed — using rule-based fallback", comm)
            med = _aggregate_verdicts({}, {}, {})

    except Exception as exc:
        logger.exception("recommendation/%s: unexpected error in agent pipeline — %s", comm, exc)
        med = _aggregate_verdicts({}, {}, {})

    # Merge mediator output over deterministic base
    result = {**base, **med}

    # Forward new structured fields from individual agents
    result["agentKeyDatapoints"] = {
        "optimist":  opt.get("key_datapoints", []),
        "pessimist": pess.get("key_datapoints", []),
        "risk":      risk.get("key_datapoints", []),
    }
    if pess.get("loss_per_quintal") is not None:
        result["lossPerQuintal"] = pess["loss_per_quintal"]
    if risk.get("floor_gap_rs") is not None:
        result["floorGapRs"] = risk["floor_gap_rs"]

    # Staging split computed from the *final* merged risk + confidence (not base alone)
    sell_pct, hold_pct = compute_staging(
        result["riskLevel"],
        result["priceTrend"],
        result["confidenceLabel"],
    )
    result["sellPctNow"] = sell_pct
    result["holdPct"]    = hold_pct

    if ai_ran:
        recommendation_cache.set(commodity, result)
    else:
        logger.warning("recommendation/%s: result NOT cached (rule-based fallback)", commodity)
    return result
