from __future__ import annotations

import pandas as pd


def _rank_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").replace([float("inf"), -float("inf")], pd.NA)
    valid = numeric.dropna()
    if valid.empty or valid.nunique() <= 1:
        return pd.Series(0.5, index=series.index, dtype="float64")

    lower = valid.quantile(0.01)
    upper = valid.quantile(0.99)
    clipped = numeric.clip(lower=lower, upper=upper)
    ranked = clipped.rank(method="average", pct=True, ascending=higher_is_better)
    return ranked.fillna(0.5).astype("float64")


def _score_column(frame: pd.DataFrame, column: str, higher_is_better: bool = True) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0.5, index=frame.index, dtype="float64")
    return _rank_score(frame[column], higher_is_better)


def score_stocks(factors: pd.DataFrame, regime_state: str | None = None) -> pd.DataFrame:
    if factors.empty:
        return factors.copy()

    scored = factors.copy()
    scored["momentum"] = _score_column(scored, "momentum_20d", True)
    scored["roe_score"] = _score_column(scored, "roe", True)
    scored["revenue_growth_score"] = _score_column(scored, "revenue_growth_yoy", True)
    scored["net_profit_growth_score"] = _score_column(scored, "net_profit_growth_yoy", True)
    scored["cashflow_quality_score"] = _score_column(scored, "ocf_to_profit", True)
    scored["quality"] = (
        0.40 * scored["roe_score"]
        + 0.25 * scored["revenue_growth_score"]
        + 0.20 * scored["net_profit_growth_score"]
        + 0.15 * scored["cashflow_quality_score"]
    )

    value_parts = []
    if "pe" in scored.columns:
        value_parts.append(_rank_score(scored["pe"], False))
    if "pb" in scored.columns:
        value_parts.append(_rank_score(scored["pb"], False))
    scored["value"] = sum(value_parts) / len(value_parts) if value_parts else 0.5
    scored["risk"] = _score_column(scored, "volatility_20d", False)

    scored["score"] = (
        0.35 * scored["momentum"]
        + 0.25 * scored["quality"]
        + 0.20 * scored["value"]
        + 0.20 * scored["risk"]
    ).clip(0, 1)
    scored["momentum_contribution"] = 0.35 * scored["momentum"]
    scored["quality_contribution"] = 0.25 * scored["quality"]
    scored["value_contribution"] = 0.20 * scored["value"]
    scored["risk_contribution"] = 0.20 * scored["risk"]
    scored["risk_adjust_factor"] = (0.75 + 0.25 * scored["risk"]).clip(0.75, 1.0)
    scored["regime_multiplier"] = _regime_multiplier(scored, regime_state)
    scored["final_score"] = (
        scored["score"] * scored["risk_adjust_factor"] * scored["regime_multiplier"]
    ).clip(0, 1)
    return scored.sort_values(
        ["final_score", "score", "momentum", "ts_code"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def _regime_multiplier(scored: pd.DataFrame, regime_state: str | None) -> pd.Series:
    state = regime_state or "range"
    if state == "trend":
        return (0.95 + 0.10 * scored["momentum"]).clip(0.95, 1.05)
    if state == "crash":
        return (0.80 + 0.20 * scored["risk"]).clip(0.80, 1.00)
    if state == "high_vol":
        return (0.85 + 0.15 * scored["risk"]).clip(0.85, 1.00)
    return (0.95 + 0.05 * scored["value"]).clip(0.95, 1.00)
