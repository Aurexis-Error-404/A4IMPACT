import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agents import mediator, risk_analyst, season_optimist, season_pessimist
from services import recommendation_cache
from services.insight_calculator import compute_insights

router = APIRouter()

_VALID_REC  = {"Hold", "Lean sell", "Defer", "Protect"}
_VALID_CONF = {"High confidence", "Moderate confidence", "Low confidence"}
_VALID_RISK = {"Low", "Watch", "High"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize(med: dict, base: dict) -> dict:
    rec      = med.get("recommendationLabel", "")
    conf     = med.get("confidenceLabel", "")
    risk     = med.get("riskLevel", "")
    rationale = med.get("recommendationRationale", "")
    return {
        "recommendationLabel":  rec      if rec      in _VALID_REC  else base["recommendationLabel"],
        "confidenceLabel":      conf     if conf     in _VALID_CONF else "Moderate confidence",
        "riskLevel":            risk     if risk     in _VALID_RISK else base["riskLevel"],
        "recommendationRationale": rationale if isinstance(rationale, str) and rationale
                                              else base["recommendationRationale"],
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
        # --- Handshake ---
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
        records = store.series_by_key[(group, comm)]
        base = compute_insights(group, comm, records)

        opt, pess, risk_res = {}, {}, {}

        # --- Stage 1: Optimist (immediate) ---
        try:
            opt = await season_optimist.analyze(comm, group, records, delay=0)
        except Exception as exc:
            opt = {"agent": "optimist", "error": str(exc)}
        await websocket.send_json({"stage": "optimist", "data": opt, "ts": _now()})

        await asyncio.sleep(2)

        # --- Stage 2: Pessimist ---
        try:
            pess = await season_pessimist.analyze(comm, group, records, delay=0)
        except Exception as exc:
            pess = {"agent": "pessimist", "error": str(exc)}
        await websocket.send_json({"stage": "pessimist", "data": pess, "ts": _now()})

        await asyncio.sleep(2)

        # --- Stage 3: Risk Analyst ---
        try:
            risk_res = await risk_analyst.analyze(comm, group, records, delay=0)
        except Exception as exc:
            risk_res = {"agent": "risk", "error": str(exc)}
        await websocket.send_json({"stage": "risk", "data": risk_res, "ts": _now()})

        # --- Stage 4: Mediator (no extra pause — runs right after risk) ---
        try:
            med_raw = await mediator.synthesize(comm, opt, pess, risk_res, base)
            med = _sanitize(med_raw, base)
        except Exception:
            med = _fallback_verdict(opt, pess, risk_res, base)
        await websocket.send_json({"stage": "mediator", "data": med, "ts": _now()})

        # Populate cache so REST endpoint benefits from this run
        recommendation_cache.set(commodity, {**base, **med})

        await websocket.send_json({"stage": "done", "ts": _now()})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"stage": "error", "error": str(exc)})
        except Exception:
            pass
