from __future__ import annotations

from typing import Any

from risk.drawdown_guard import apply_drawdown_guard, estimate_portfolio_drawdown
from risk.exposure_risk import calculate_industry_exposure, cap_industry_exposure


DEFAULT_MAX_POSITION_PER_STOCK = 0.10
DEFAULT_MAX_INDUSTRY_WEIGHT = 0.30
DEFAULT_DRAWDOWN_THRESHOLD = 0.08


def build_portfolio(
    picks: list[dict[str, Any]],
    max_position_per_stock: float = DEFAULT_MAX_POSITION_PER_STOCK,
    max_industry_weight: float = DEFAULT_MAX_INDUSTRY_WEIGHT,
    drawdown_threshold: float = DEFAULT_DRAWDOWN_THRESHOLD,
) -> dict[str, Any]:
    if not picks:
        return _empty_portfolio(max_position_per_stock, max_industry_weight, drawdown_threshold)

    positions = _initial_score_weighted_positions(picks)
    positions = _cap_position_weights(positions, max_position_per_stock)
    positions, industry_exposure = cap_industry_exposure(positions, max_industry_weight)

    estimated_drawdown = estimate_portfolio_drawdown(positions)
    positions, drawdown_guard = apply_drawdown_guard(
        positions,
        estimated_drawdown=estimated_drawdown,
        threshold=drawdown_threshold,
    )

    positions = _round_positions(positions)
    industry_exposure = calculate_industry_exposure(positions)
    invested_weight = round(sum(position["weight"] for position in positions), 6)
    cash_weight = round(max(0.0, 1.0 - invested_weight), 6)
    expected_volatility = round(
        sum(
            position["weight"] * float((position.get("metrics") or {}).get("volatility_20d") or 0)
            for position in positions
        ),
        6,
    )

    return {
        "positions": positions,
        "risk": {
            "max_position_per_stock": max_position_per_stock,
            "max_industry_weight": max_industry_weight,
            "industry_exposure": industry_exposure,
            "estimated_drawdown": estimated_drawdown,
            "drawdown_guard": drawdown_guard,
            "expected_volatility": expected_volatility,
            "cash_weight": cash_weight,
            "risk_level": _risk_level(estimated_drawdown, drawdown_threshold),
        },
    }


def _initial_score_weighted_positions(picks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for pick in picks:
        weight_score = pick.get("final_score") or pick.get("score") or 0
        scored.append((pick, max(float(weight_score), 0.0)))

    total_score = sum(score for _, score in scored)
    if total_score <= 0:
        base_weight = 1.0 / len(scored)
        return [dict(pick, weight=base_weight) for pick, _ in scored]

    return [dict(pick, weight=score / total_score) for pick, score in scored]


def _cap_position_weights(
    positions: list[dict[str, Any]],
    max_position_per_stock: float,
) -> list[dict[str, Any]]:
    capped = [dict(position) for position in positions]
    for _ in range(10):
        excess = 0.0
        receivers = []
        for position in capped:
            weight = float(position["weight"])
            if weight > max_position_per_stock:
                excess += weight - max_position_per_stock
                position["weight"] = max_position_per_stock
            elif weight < max_position_per_stock:
                receivers.append(position)

        if excess <= 1e-12 or not receivers:
            break

        receiver_total = sum(float(position["weight"]) for position in receivers)
        if receiver_total <= 0:
            spread = excess / len(receivers)
            for position in receivers:
                position["weight"] += spread
        else:
            for position in receivers:
                position["weight"] += excess * float(position["weight"]) / receiver_total

    return capped


def _round_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rounded = []
    for position in positions:
        item = dict(position)
        item["weight"] = round(float(item.get("weight") or 0), 6)
        rounded.append(item)
    return rounded


def _risk_level(estimated_drawdown: float, threshold: float) -> str:
    if estimated_drawdown >= threshold:
        return "high"
    if estimated_drawdown >= threshold * 0.6:
        return "medium"
    return "low"


def _empty_portfolio(
    max_position_per_stock: float,
    max_industry_weight: float,
    drawdown_threshold: float,
) -> dict[str, Any]:
    return {
        "positions": [],
        "risk": {
            "max_position_per_stock": max_position_per_stock,
            "max_industry_weight": max_industry_weight,
            "industry_exposure": {},
            "estimated_drawdown": 0.0,
            "drawdown_guard": {
                "triggered": False,
                "threshold": drawdown_threshold,
                "scale": 1.0,
            },
            "expected_volatility": 0.0,
            "cash_weight": 1.0,
            "risk_level": "low",
        },
    }
