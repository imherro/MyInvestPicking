from __future__ import annotations

from typing import Any

import pandas as pd

from config.settings import DEFAULT_TOP_N
from engine.data_loader import TushareDataLoader, format_api_date
from engine.factor_engine import compute_factors
from engine.scoring import score_stocks
from engine.universe import filter_universe


def _round_float(value: Any, digits: int = 4) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), digits)


def _to_pick(row: pd.Series) -> dict[str, Any]:
    return {
        "code": row["ts_code"],
        "name": row.get("name"),
        "industry": row.get("industry"),
        "score": _round_float(row.get("score")),
        "factors": {
            "momentum": _round_float(row.get("momentum")),
            "quality": _round_float(row.get("quality")),
            "value": _round_float(row.get("value")),
            "risk": _round_float(row.get("risk")),
        },
        "metrics": {
            "momentum_20d": _round_float(row.get("momentum_20d")),
            "volatility_20d": _round_float(row.get("volatility_20d")),
            "roe": _round_float(row.get("roe")),
            "pe": _round_float(row.get("pe")),
            "pb": _round_float(row.get("pb")),
            "close": _round_float(row.get("close")),
        },
    }


def build_stock_picks(
    trade_date: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    loader: TushareDataLoader | None = None,
) -> dict[str, Any]:
    active_loader = loader or TushareDataLoader()
    market_data = active_loader.load_market_data(trade_date)
    tradable_universe = filter_universe(market_data.stock_basic, market_data.daily)
    tradable_codes = set(tradable_universe["ts_code"].astype(str))

    factors = compute_factors(market_data)
    if not factors.empty:
        factors = factors[factors["ts_code"].isin(tradable_codes)]

    scored = score_stocks(factors)
    selected = scored.head(max(top_n, 0))

    return {
        "status": "ok",
        "date": format_api_date(market_data.trade_date),
        "source": market_data.source,
        "mock_mode": market_data.mock_mode,
        "universe_size": int(len(tradable_universe)),
        "data": [_to_pick(row) for _, row in selected.iterrows()],
    }
