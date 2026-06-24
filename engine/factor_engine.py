from __future__ import annotations

import pandas as pd

from engine.data_loader import MarketData


def compute_factors(market_data: MarketData) -> pd.DataFrame:
    daily = market_data.daily.copy()
    if daily.empty:
        return pd.DataFrame()

    daily["close"] = pd.to_numeric(daily["close"], errors="coerce")
    daily["pct_chg"] = pd.to_numeric(daily.get("pct_chg"), errors="coerce")
    daily = daily.dropna(subset=["ts_code", "trade_date", "close"])
    daily = daily.sort_values(["trade_date", "ts_code"])

    close_wide = daily.pivot_table(index="trade_date", columns="ts_code", values="close")
    returns = close_wide.pct_change()
    latest_close = close_wide.iloc[-1]
    if len(close_wide) > 20:
        base_close = close_wide.shift(20).iloc[-1]
    else:
        base_close = close_wide.iloc[0]

    momentum_20d = latest_close / base_close - 1
    volatility_20d = returns.tail(20).std()
    latest_daily = daily.groupby("ts_code", as_index=False).tail(1)

    factors = pd.DataFrame(
        {
            "ts_code": latest_close.index.astype(str),
            "momentum_20d": momentum_20d.values,
            "volatility_20d": volatility_20d.reindex(latest_close.index).values,
            "close": latest_close.values,
        }
    )

    factors = factors.merge(latest_daily[["ts_code", "trade_date"]], on="ts_code", how="left")

    daily_basic = market_data.daily_basic.copy()
    if not daily_basic.empty:
        daily_basic = daily_basic.groupby("ts_code", as_index=False).tail(1)
        keep_columns = [
            column
            for column in ["ts_code", "pe", "pb", "roe", "turnover_rate", "volume_ratio"]
            if column in daily_basic.columns
        ]
        factors = factors.merge(daily_basic[keep_columns], on="ts_code", how="left")

    financial = market_data.financial_indicator.copy()
    if not financial.empty:
        financial = financial.rename(
            columns={
                "or_yoy": "revenue_growth_yoy",
                "netprofit_yoy": "net_profit_growth_yoy",
            }
        )
        financial = financial.groupby("ts_code", as_index=False).tail(1)
        keep_columns = [
            column
            for column in [
                "ts_code",
                "roe",
                "revenue_growth_yoy",
                "net_profit_growth_yoy",
                "ocf_to_profit",
            ]
            if column in financial.columns
        ]
        factors = factors.merge(
            financial[keep_columns],
            on="ts_code",
            how="left",
            suffixes=("", "_financial"),
        )
        if "roe_financial" in factors.columns:
            if "roe" in factors.columns:
                factors["roe"] = factors["roe_financial"].combine_first(factors["roe"])
            else:
                factors["roe"] = factors["roe_financial"]
            factors = factors.drop(columns=["roe_financial"])

    stock_basic = market_data.stock_basic.copy()
    if not stock_basic.empty:
        keep_columns = [
            column for column in ["ts_code", "name", "industry"] if column in stock_basic.columns
        ]
        factors = factors.merge(stock_basic[keep_columns], on="ts_code", how="left")

    for column in [
        "momentum_20d",
        "volatility_20d",
        "pe",
        "pb",
        "roe",
        "revenue_growth_yoy",
        "net_profit_growth_yoy",
        "ocf_to_profit",
    ]:
        if column in factors.columns:
            factors[column] = pd.to_numeric(factors[column], errors="coerce")

    return factors
