import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agents import mediator, risk_analyst, season_optimist, season_pessimist
from services import recommendation_cache
from services.insight_calculator import compute_insights
from services.pre_analysis_enricher import enrich
from services.staging import compute_staging

router = APIRouter()

_VALID_REC  = {"Hold", "Lean sell", "Defer", "Protect"}
_VALID_CONF = {"High confidence", "Moderate confidence", "Low confidence"}
_VALID_RISK = {"Low", "Watch", "High"}

_LABEL_MAP: dict[str, str] = {
    "hold":                "Hold",
    "lean sell":           "Lean sell",
    "lean_sell":           "Lean sell",
    "leansell":            "Lean sell",
    "defer":               "Defer",
    "protect":             "Protect",
    "high confidence":     "High confidence",
    "high_confidence":     "High confidence",
    "moderate confidence": "Moderate confidence",
    "moderate_confidence": "Moderate confidence",
    "low confidence":      "Low confidence",
    "low_confidence":      "Low confidence",
    "low":                 "Low",
    "watch":               "Watch",
    "high":                "High",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise(raw: str) -> str:
    return _LABEL_MAP.get(raw.strip().lower(), raw) if isinstance(raw, str) else raw


def _sanitize(med: dict, base: dict) -> dict:
    rec       = _normalise(med.get("recommendationLabel", ""))
    conf      = _normalise(med.get("confidenceLabel", ""))
    risk      = _normalise(med.get("riskLevel", ""))
    rationale = med.get("recommendationRationale", "")
    timing    = med.get("actionable_timing", "")
    conflict  = med.get("conflict_score", "LOW")
    return {
        "recommendationLabel":    rec  if rec  in _VALID_REC  else base["recommendationLabel"],
        "confidenceLabel":        conf if conf in _VALID_CONF else "Moderate confidence",
        "riskLevel":              risk if risk in _VALID_RISK else base["riskLevel"],
        "recommendationRationale": rationale if isinstance(rationale, str) and rationale
                                               else base["recommendationRationale"],
        "actionableTiming": timing if isinstance(timing, str) else "",
        "conflictScore":    conflict if conflict in {"LOW", "MEDIUM", "HIGH"} else "LOW",
    }


def _fallback_verdict(opt: dict, pess: dict, risk_res: dict, base: dict) -> dict:
    verdicts = [opt.get("verdict", ""), pess.get("verdict", ""), risk_res.get("verdict", "")]
    if verdicts.count("PROTECT") >= 2:
        label = "Protect"
    elif verdicts.count("DEFER") >= 2:
        label = "Defer"
    elif verdicts.count("LEAN_SELL") >= 2:
        label = "Lean sell"
    else:
        label = "Hold"
    rl = risk_res.get("risk_level", base["riskLevel"])
    return {
        "recommendationLabel": label,
        "confidenceLabel": "Low confidence",
        "riskLevel": rl if rl in _VALID_RISK else base["riskLevel"],
        "recommendationRationale": base["recommendationRationale"],
    }


@router.websocket("/ws")
async def debate_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        msg = await websocket.receive_json()
        if msg.get("action") != "start" or not msg.get("commodity"):
            await websocket.send_json({"stage": "error", "error": "expected {action:'start',commodity:'<name>'}"})
            return

        commodity: str = msg["commodity"]
        store = websocket.app.state.store

        match = next(((g, c) for g, c in store.series_by_key if c == commodity), None)
        if not match:
            await websocket.send_json({"stage": "error", "error": "commodity_not_found", "commodity": commodity})
            return

        group, comm = match
        records  = store.series_by_key[(group, comm)]
        base     = compute_insights(group, comm, records)
        enriched = enrich(records)

        opt, pess, risk_res = {}, {}, {}

        # Stage 1: Optimist
        try:
            opt = await season_optimist.analyze(comm, group, records, delay=0, enriched=enriched)
        except Exception as exc:
            opt = {"agent": "optimist", "error": str(exc)}
        await websocket.send_json({"stage": "optimist", "data": opt, "ts": _now()})
        await asyncio.sleep(2)

        # Stage 2: Pessimist
        try:
            pess = await season_pessimist.analyze(comm, group, records, delay=0, enriched=enriched)
        except Exception as exc:
            pess = {"agent": "pessimist", "error": str(exc)}
        await websocket.send_json({"stage": "pessimist", "data": pess, "ts": _now()})
        await asyncio.sleep(2)

        # Stage 3: Risk Analyst
        try:
            risk_res = await risk_analyst.analyze(comm, group, records, delay=0, enriched=enriched)
        except Exception as exc:
            risk_res = {"agent": "risk", "error": str(exc)}
        await websocket.send_json({"stage": "risk", "data": risk_res, "ts": _now()})

        # Stage 4: Mediator
        try:
            med_raw = await mediator.synthesize(comm, opt, pess, risk_res, base, enriched=enriched)
            med = _sanitize(med_raw, base)
        except Exception:
            med = _fallback_verdict(opt, pess, risk_res, base)
        # DebatePanel reads snake_case keys from the mediator; include both forms
        med_ws = {
            **med,
            "conflict_score":   med.get("conflictScore", "LOW"),
            "actionable_timing": med.get("actionableTiming", ""),
        }
        await websocket.send_json({"stage": "mediator", "data": med_ws, "ts": _now()})

        # Compute staging and write full result to cache
        sell_pct, hold_pct = compute_staging(
            med["riskLevel"], base["priceTrend"], med["confidenceLabel"]
        )
        full_result = {
            **base, **med,
            "sellPctNow": sell_pct,
            "holdPct":    hold_pct,
        }
        recommendation_cache.set(commodity, full_result)

        # Push real-time alert event if commodity is under pressure
        if med["riskLevel"] in ("High", "Watch"):
            severity = "red" if med["riskLevel"] == "High" else "amber"
            delta_pct = base.get("latestDeltaPct", 0)
            headline = (
                f"{commodity} {abs(delta_pct) * 100:.1f}% below MSP — "
                f"{med['recommendationLabel']} recommended"
                if delta_pct < 0
                else f"{commodity} near MSP — {med['riskLevel']} risk signal"
            )
            await websocket.send_json({
                "stage":    "alert",
                "severity": severity,
                "commodity": commodity,
                "headline": headline,
                "riskLevel": med["riskLevel"],
                "ts":       _now(),
            })

        await websocket.send_json({"stage": "done", "ts": _now()})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"stage": "error", "error": str(exc)})
        except Exception:
            pass
