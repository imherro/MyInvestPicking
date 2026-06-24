from __future__ import annotations

import pandas as pd


ST_PATTERN = r"(?:^|\*)ST|退"


def filter_universe(stock_basic: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    if stock_basic.empty:
        return stock_basic.copy()

    filtered = stock_basic.copy()
    names = filtered["name"].fillna("").astype(str)
    filtered = filtered[~names.str.contains(ST_PATTERN, case=False, regex=True)]

    if daily.empty or "ts_code" not in daily.columns:
        return filtered.reset_index(drop=True)

    latest_trade_date = daily["trade_date"].max()
    latest_daily = daily[daily["trade_date"] == latest_trade_date]
    if "is_suspended" in latest_daily.columns:
        latest_daily = latest_daily[latest_daily["is_suspended"] != True]  # noqa: E712

    tradable_codes = set(latest_daily["ts_code"].dropna().astype(str))
    filtered = filtered[filtered["ts_code"].isin(tradable_codes)]
    return filtered.reset_index(drop=True)
