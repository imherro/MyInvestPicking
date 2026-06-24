from fastapi import APIRouter, Query

from config.settings import DEFAULT_TOP_N
from strategy.core_strategy import build_stock_picks


router = APIRouter(prefix="/api", tags=["stock"])


@router.get("/picks")
def get_picks(
    date: str | None = Query(default=None, description="Trade date as YYYY-MM-DD or YYYYMMDD"),
    top_n: int = Query(default=DEFAULT_TOP_N, ge=1, le=100),
) -> dict[str, object]:
    return build_stock_picks(trade_date=date, top_n=top_n)
