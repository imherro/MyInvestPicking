from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import random
from typing import Optional

import pandas as pd

from config.settings import FORCE_MOCK_DATA, MOCK_STOCK_COUNT, TUSHARE_TOKEN


@dataclass(frozen=True)
class MarketData:
    trade_date: str
    stock_basic: pd.DataFrame
    daily: pd.DataFrame
    daily_basic: pd.DataFrame
    mock_mode: bool
    source: str


def normalize_trade_date(value: Optional[str] = None) -> str:
    if value is None:
        return date.today().strftime("%Y%m%d")

    raw = value.strip()
    if len(raw) == 8 and raw.isdigit():
        return raw
    return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y%m%d")


def format_api_date(trade_date: str) -> str:
    return datetime.strptime(trade_date, "%Y%m%d").strftime("%Y-%m-%d")


class TushareDataLoader:
    def __init__(self, token: str | None = None, force_mock: bool | None = None) -> None:
        self.token = token if token is not None else TUSHARE_TOKEN
        self.force_mock = FORCE_MOCK_DATA if force_mock is None else force_mock

    def get_universe(self) -> list[str]:
        return self.load_market_data().stock_basic["ts_code"].tolist()

    def get_daily_data(self, trade_date: str | None = None) -> pd.DataFrame:
        market_data = self.load_market_data(trade_date)
        return market_data.daily.merge(
            market_data.daily_basic,
            on=["ts_code", "trade_date"],
            how="left",
            suffixes=("", "_basic"),
        )

    def load_market_data(self, trade_date: str | None = None) -> MarketData:
        normalized_date = normalize_trade_date(trade_date)
        if not self.force_mock and self.token:
            try:
                return self._load_tushare_market_data(normalized_date)
            except Exception:
                pass
        return self._load_mock_market_data(normalized_date)

    def _load_tushare_market_data(self, trade_date: str) -> MarketData:
        import tushare as ts

        ts.set_token(self.token)
        pro = ts.pro_api(self.token)
        start_date = (
            datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=90)
        ).strftime("%Y%m%d")

        stock_basic = pro.stock_basic(
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,list_date",
        )
        daily = pro.daily(start_date=start_date, end_date=trade_date)
        if daily.empty:
            raise ValueError("Tushare returned no daily rows")

        latest_trade_date = str(daily["trade_date"].max())
        daily_basic = pro.daily_basic(
            trade_date=latest_trade_date,
            fields="ts_code,trade_date,pe,pb,turnover_rate,volume_ratio",
        )
        if daily_basic.empty:
            raise ValueError("Tushare returned no daily_basic rows")

        return MarketData(
            trade_date=latest_trade_date,
            stock_basic=stock_basic,
            daily=daily,
            daily_basic=daily_basic,
            mock_mode=False,
            source="tushare",
        )

    def _load_mock_market_data(self, trade_date: str) -> MarketData:
        rng = random.Random(int(trade_date))
        end = pd.Timestamp(datetime.strptime(trade_date, "%Y%m%d"))
        dates = pd.bdate_range(end=end, periods=45)

        stocks = []
        daily_rows = []
        basic_rows = []
        industries = ["Bank", "Tech", "Pharma", "Consumer", "Energy", "Auto"]

        for idx in range(MOCK_STOCK_COUNT):
            symbol = f"{idx + 1:06d}"
            suffix = "SZ" if idx % 2 == 0 else "SH"
            ts_code = f"{symbol}.{suffix}"
            is_st = idx in {4, 17}
            is_suspended = idx in {8, 23}
            name = f"{'*ST ' if is_st else ''}MockStock{idx + 1:02d}"
            industry = industries[idx % len(industries)]
            stocks.append(
                {
                    "ts_code": ts_code,
                    "symbol": symbol,
                    "name": name,
                    "area": "CN",
                    "industry": industry,
                    "list_date": "20180101",
                }
            )

            base_price = 8 + idx * 0.7 + rng.random() * 2
            drift = 0.0005 + (idx % 7) * 0.0006
            prices = []
            last_price = base_price
            for date_index, day in enumerate(dates):
                shock = rng.uniform(-0.018, 0.022)
                last_price = max(2.0, last_price * (1 + drift + shock))
                prices.append((day.strftime("%Y%m%d"), round(last_price, 2)))

                if date_index == len(dates) - 1 and is_suspended:
                    continue

                pre_close = prices[-2][1] if len(prices) > 1 else base_price
                pct_chg = (last_price / pre_close - 1) * 100
                daily_rows.append(
                    {
                        "ts_code": ts_code,
                        "trade_date": day.strftime("%Y%m%d"),
                        "close": round(last_price, 2),
                        "pre_close": round(pre_close, 2),
                        "pct_chg": round(pct_chg, 4),
                        "vol": round(10000 + rng.random() * 90000, 2),
                        "amount": round(last_price * (1000 + rng.random() * 5000), 2),
                        "is_suspended": is_suspended
                        and date_index == len(dates) - 1,
                    }
                )

            latest_date = dates[-1].strftime("%Y%m%d")
            pe = 9 + (idx % 12) * 2.3 + rng.random() * 3
            pb = 0.8 + (idx % 8) * 0.22 + rng.random() * 0.2
            roe = 6 + (idx % 10) * 1.6 + rng.random() * 2
            basic_rows.append(
                {
                    "ts_code": ts_code,
                    "trade_date": latest_date,
                    "pe": round(pe, 4),
                    "pb": round(pb, 4),
                    "roe": round(roe, 4),
                    "turnover_rate": round(1 + rng.random() * 6, 4),
                    "volume_ratio": round(0.7 + rng.random() * 1.8, 4),
                }
            )

        return MarketData(
            trade_date=dates[-1].strftime("%Y%m%d"),
            stock_basic=pd.DataFrame(stocks),
            daily=pd.DataFrame(daily_rows),
            daily_basic=pd.DataFrame(basic_rows),
            mock_mode=True,
            source="mock",
        )
