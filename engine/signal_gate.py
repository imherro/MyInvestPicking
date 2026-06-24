from __future__ import annotations

from typing import Any

BUY_THRESHOLD = 0.62
HOLD_THRESHOLD = 0.48
MIN_BUY_SCORE = 0.38
MIN_HOLD_SCORE = 0.30


def build_signal_decision(
    position: dict[str, Any],
    tradability: dict[str, Any],
    confidence: dict[str, Any],
    market_regime: dict[str, Any],
    correlation_context: dict[str, Any],
    backtest_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final_score = _to_float(position.get("final_score"), 0.0)
    confidence_score = _to_float(confidence.get("confidence"), 0.0)
    action = _action(
        final_score=final_score,
        confidence_score=confidence_score,
        tradability=tradability,
        market_regime=market_regime,
        correlation_context=correlation_context,
        backtest_context=backtest_context or {},
    )
    position_size = _position_size(position, action)
    return {
        "action": action,
        "confidence": round(confidence_score, 4),
        "position_size": position_size,
        "reason": _reason_payload(
            position=position,
            tradability=tradability,
            confidence=confidence,
            market_regime=market_regime,
            correlation_context=correlation_context,
            backtest_context=backtest_context or {},
            action=action,
        ),
    }


def _action(
    final_score: float,
    confidence_score: float,
    tradability: dict[str, Any],
    market_regime: dict[str, Any],
    correlation_context: dict[str, Any],
    backtest_context: dict[str, Any],
) -> str:
    if not tradability.get("tradable"):
        return "NO_TRADE"
    if backtest_context.get("block_buy"):
        return "NO_TRADE"
    if backtest_context.get("caution") and confidence_score < 0.75:
        return "HOLD"
    if str(market_regime.get("state") or "") == "crash" and confidence_score < 0.80:
        return "NO_TRADE"
    if correlation_context.get("cluster_block") and confidence_score < 0.75:
        return "HOLD"
    if final_score >= MIN_BUY_SCORE and confidence_score >= BUY_THRESHOLD:
        return "BUY"
    if final_score >= MIN_HOLD_SCORE and confidence_score >= HOLD_THRESHOLD:
        return "HOLD"
    return "NO_TRADE"


def _position_size(position: dict[str, Any], action: str) -> float:
    if action != "BUY":
        return 0.0
    return round(_to_float(position.get("weight"), 0.0), 6)


def _reason_payload(
    position: dict[str, Any],
    tradability: dict[str, Any],
    confidence: dict[str, Any],
    market_regime: dict[str, Any],
    correlation_context: dict[str, Any],
    backtest_context: dict[str, Any],
    action: str,
) -> dict[str, Any]:
    return {
        "decision": action,
        "final_score": _to_float(position.get("final_score"), 0.0),
        "regime": market_regime.get("state"),
        "tradable": tradability.get("tradable"),
        "tradability_reasons": tradability.get("reasons", []),
        "confidence_components": confidence.get("components", {}),
        "correlation": correlation_context,
        "backtest": backtest_context,
    }


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
