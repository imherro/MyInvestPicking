from __future__ import annotations

from typing import Any

from engine.signal_confidence import calculate_signal_confidence
from engine.signal_gate import build_signal_decision
from engine.tradability_engine import assess_tradability


def build_final_signals(
    positions: list[dict[str, Any]],
    market_regime: dict[str, Any],
    correlation_risk: dict[str, Any],
    backtest_metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    signals = []
    for position in positions:
        tradability = assess_tradability(position)
        confidence = calculate_signal_confidence(position, market_regime, tradability)
        correlation_context = _correlation_context(position, correlation_risk)
        decision = build_signal_decision(
            position=position,
            tradability=tradability,
            confidence=confidence,
            market_regime=market_regime,
            correlation_context=correlation_context,
            backtest_context=_backtest_context(backtest_metrics or {}),
        )
        signals.append(
            {
                "code": position.get("code"),
                "name": position.get("name"),
                "industry": position.get("industry"),
                "weight": position.get("weight"),
                "final_score": position.get("final_score"),
                "score": position.get("score"),
                "risk_adjust_factor": position.get("risk_adjust_factor"),
                "regime_multiplier": position.get("regime_multiplier"),
                "factor_health_score": position.get("factor_health_score"),
                "exchange_risk_multiplier": position.get("exchange_risk_multiplier"),
                "liquidity_risk_multiplier": position.get("liquidity_risk_multiplier"),
                "factors": position.get("factors", {}),
                "metrics": position.get("metrics", {}),
                "action": decision["action"],
                "confidence": decision["confidence"],
                "position_size": decision["position_size"],
                "tradability": tradability,
                "signal_confidence": confidence,
                "reason": decision["reason"],
            }
        )
    return sorted(
        signals,
        key=lambda item: (
            _action_rank(str(item.get("action"))),
            -float(item.get("confidence") or 0),
            -float(item.get("final_score") or 0),
            str(item.get("code") or ""),
        ),
    )


def summarize_signals(signals: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"BUY": 0, "HOLD": 0, "NO_TRADE": 0}
    for signal in signals:
        action = str(signal.get("action") or "NO_TRADE")
        counts[action] = counts.get(action, 0) + 1
    buy_exposure = sum(
        float(signal.get("position_size") or 0)
        for signal in signals
        if signal.get("action") == "BUY"
    )
    average_confidence = (
        sum(float(signal.get("confidence") or 0) for signal in signals) / len(signals)
        if signals
        else 0.0
    )
    return {
        "counts": counts,
        "buy_exposure": round(buy_exposure, 6),
        "average_confidence": round(average_confidence, 4),
    }


def _correlation_context(
    position: dict[str, Any],
    correlation_risk: dict[str, Any],
) -> dict[str, Any]:
    code = str(position.get("code") or "")
    for cluster in correlation_risk.get("clusters", []):
        codes = set(cluster.get("codes", []))
        if code in codes:
            avg_correlation = float(cluster.get("avg_correlation") or 0)
            return {
                "cluster_id": cluster.get("id"),
                "cluster_size": cluster.get("size"),
                "avg_correlation": round(avg_correlation, 4),
                "cluster_block": avg_correlation >= float(correlation_risk.get("threshold", 0.75)),
            }
    return {
        "cluster_id": None,
        "cluster_size": 0,
        "avg_correlation": 0.0,
        "cluster_block": False,
    }


def _backtest_context(metrics: dict[str, Any]) -> dict[str, Any]:
    sharpe = float(metrics.get("sharpe") or 0)
    max_drawdown = float(metrics.get("max_drawdown") or 0)
    return {
        "sharpe": round(sharpe, 6),
        "max_drawdown": round(max_drawdown, 6),
        "turnover": metrics.get("turnover"),
        "block_buy": sharpe < 0 or max_drawdown <= -0.08,
        "caution": sharpe < 0.50 or max_drawdown <= -0.05,
    }


def _action_rank(action: str) -> int:
    return {"BUY": 0, "HOLD": 1, "NO_TRADE": 2}.get(action, 3)
