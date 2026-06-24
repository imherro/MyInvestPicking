from __future__ import annotations

from typing import Any

from risk.portfolio_builder import build_portfolio


def build_risk_managed_portfolio(picks: list[dict[str, Any]]) -> dict[str, Any]:
    return build_portfolio(picks)
