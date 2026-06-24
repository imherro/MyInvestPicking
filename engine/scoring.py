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


def score_stocks(factors: pd.DataFrame) -> pd.DataFrame:
    if factors.empty:
        return factors.copy()

    scored = factors.copy()
    scored["momentum"] = _score_column(scored, "momentum_20d", True)
    scored["quality"] = _score_column(scored, "roe", True)

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
    return scored.sort_values(["score", "momentum"], ascending=False).reset_index(drop=True)
