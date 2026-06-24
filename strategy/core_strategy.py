from __future__ import annotations

from typing import Any

import pandas as pd

from backtest.engine import run_backtest
from config.settings import DEFAULT_TOP_N
from engine.data_loader import TushareDataLoader, format_api_date
from engine.factor_decay import add_factor_health, summarize_factor_health
from engine.factor_engine import compute_factors
from engine.liquidity import filter_liquidity
from engine.market_features import compute_market_features
from engine.market_regime import detect_market_regime
from engine.portfolio_stability import compute_portfolio_stability
from engine.scoring import score_stocks
from engine.snapshot import build_universe_hash, create_snapshot
from engine.universe import filter_universe
from risk.concentration_risk import evaluate_concentration_risk
from risk.correlation_engine import compute_correlation_risk
from risk.dynamic_risk_allocator import allocate_dynamic_risk_budget
from risk.risk_engine import build_risk_managed_portfolio


def _round_float(value: Any, digits: int = 4) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), digits)


def _to_pick(row: pd.Series) -> dict[str, Any]:
    factors = {
        "momentum": _round_float(row.get("momentum")),
        "quality": _round_float(row.get("quality")),
        "value": _round_float(row.get("value")),
        "risk": _round_float(row.get("risk")),
    }
    return {
        "code": row["ts_code"],
        "name": row.get("name"),
        "industry": row.get("industry"),
        "score": _round_float(row.get("score")),
        "final_score": _round_float(row.get("final_score")),
        "risk_adjust_factor": _round_float(row.get("risk_adjust_factor")),
        "regime_multiplier": _round_float(row.get("regime_multiplier")),
        "factor_health_score": _round_float(row.get("factor_health_score")),
        "exchange_risk_multiplier": _round_float(row.get("exchange_risk_multiplier")),
        "liquidity_risk_multiplier": _round_float(row.get("liquidity_risk_multiplier")),
        "factors": factors,
        "contribution": {
            "momentum": _round_float(row.get("momentum_contribution")),
            "quality": _round_float(row.get("quality_contribution")),
            "value": _round_float(row.get("value_contribution")),
            "risk": _round_float(row.get("risk_contribution")),
        },
        "metrics": {
            "momentum_5d": _round_float(row.get("momentum_5d")),
            "momentum_20d": _round_float(row.get("momentum_20d")),
            "volatility_20d": _round_float(row.get("volatility_20d")),
            "observation_count": _round_float(row.get("observation_count"), 0),
            "latest_amount": _round_float(row.get("latest_amount")),
            "latest_vol": _round_float(row.get("latest_vol")),
            "latest_pct_chg": _round_float(row.get("latest_pct_chg")),
            "roe": _round_float(row.get("roe")),
            "revenue_growth_yoy": _round_float(row.get("revenue_growth_yoy")),
            "net_profit_growth_yoy": _round_float(row.get("net_profit_growth_yoy")),
            "ocf_to_profit": _round_float(row.get("ocf_to_profit")),
            "pe": _round_float(row.get("pe")),
            "pb": _round_float(row.get("pb")),
            "close": _round_float(row.get("close")),
            "turnover_rate": _round_float(row.get("turnover_rate")),
            "volume_ratio": _round_float(row.get("volume_ratio")),
            "list_age_days": _round_float(row.get("list_age_days"), 0),
        },
        "reason": _build_reason(factors),
    }


def _build_reason(factors: dict[str, float | None]) -> list[str]:
    readable = []
    labels = {
        "momentum": "Momentum",
        "quality": "Quality",
        "value": "Valuation",
        "risk": "Risk control",
    }
    for key, label in labels.items():
        value = factors.get(key)
        if value is not None:
            readable.append(f"{label} rank {value:.2f}")
    return readable


def build_stock_picks(
    trade_date: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    loader: TushareDataLoader | None = None,
) -> dict[str, Any]:
    active_loader = loader or TushareDataLoader()
    market_data = active_loader.load_market_data(trade_date)
    market_features = compute_market_features(market_data.daily)
    market_regime = detect_market_regime(market_features)
    risk_budget = allocate_dynamic_risk_budget(market_regime)
    tradable_universe = filter_universe(market_data.stock_basic, market_data.daily)
    tradable_codes = set(tradable_universe["ts_code"].astype(str))

    factors = compute_factors(market_data)
    if not factors.empty:
        factors = factors[factors["ts_code"].isin(tradable_codes)]
    factors = filter_liquidity(factors)
    factors = add_factor_health(factors)
    factor_health = summarize_factor_health(factors)

    scored = score_stocks(factors, regime_state=str(market_regime["state"]))
    selected = scored.head(max(top_n, 0))
    results = [_to_pick(row) for _, row in selected.iterrows()]
    correlation_risk = compute_correlation_risk(
        market_data.daily,
        [pick["code"] for pick in results],
    )
    portfolio_result = build_risk_managed_portfolio(
        results,
        risk_budget=risk_budget,
        correlation_clusters=correlation_risk["clusters"],
    )
    concentration_risk = evaluate_concentration_risk(
        portfolio_result["positions"],
        correlation_risk["clusters"],
    )
    portfolio_stability = compute_portfolio_stability(portfolio_result["positions"])
    backtest = run_backtest(market_data, portfolio_result["positions"])
    universe_hash = build_universe_hash(tradable_universe["ts_code"].astype(str))
    snapshot = create_snapshot(
        trading_date=format_api_date(market_data.trade_date),
        data_version=market_data.data_version,
        universe_hash=universe_hash,
        source=market_data.source,
        mock_mode=market_data.mock_mode,
        results={
            "picks": results,
            "portfolio": portfolio_result["positions"],
            "risk": portfolio_result["risk"],
            "market_regime": market_regime,
            "risk_budget": risk_budget,
            "correlation_risk": correlation_risk,
            "factor_health": factor_health,
            "concentration_risk": concentration_risk,
            "portfolio_stability": portfolio_stability,
            "backtest": {
                "metrics": backtest["metrics"],
                "assumptions": backtest["assumptions"],
            },
        },
    )

    return {
        "status": "ok",
        "date": format_api_date(market_data.trade_date),
        "trading_date": format_api_date(market_data.trade_date),
        "source": market_data.source,
        "mock_mode": market_data.mock_mode,
        "data_version": market_data.data_version,
        **snapshot,
        "market_features": market_features,
        "market_regime": market_regime,
        "risk_budget": risk_budget,
        "correlation_risk": correlation_risk,
        "factor_health": factor_health,
        "concentration_risk": concentration_risk,
        "portfolio_stability": portfolio_stability,
        "backtest": backtest,
        "universe_size": int(len(tradable_universe)),
        "portfolio": portfolio_result["positions"],
        "risk": portfolio_result["risk"],
        "data": results,
    }
