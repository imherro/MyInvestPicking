import os
import warnings

os.environ["MYINVESTPICKING_FORCE_MOCK"] = "1"

from starlette.exceptions import StarletteDeprecationWarning

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
    category=StarletteDeprecationWarning,
)

from fastapi.testclient import TestClient

from app.main import app
from engine.tradability_engine import assess_tradability
from risk.portfolio_builder import build_portfolio


client = TestClient(app)


def test_index_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "MyInvestPicking" in response.text


def test_picks_endpoint_returns_structured_results() -> None:
    response = client.get("/api/picks?top_n=5")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["source"] == "mock"
    assert payload["mock_mode"] is True
    assert payload["data_version"]
    assert payload["factor_version"] == "v2"
    assert payload["snapshot_id"]
    assert payload["universe_hash"]
    assert len(payload["data"]) == 5
    assert len(payload["portfolio"]) == 5
    assert len(payload["signals"]) == 5
    assert payload["signal_summary"]["counts"]
    assert payload["market_regime"]["state"] in {"trend", "range", "crash", "high_vol"}
    assert 0 <= payload["market_regime"]["confidence"] <= 1
    assert payload["risk_budget"]["max_position_per_stock"] > 0
    assert payload["risk_budget"]["target_exposure"] <= 0.95
    assert payload["risk"]["max_position_per_stock"] == payload["risk_budget"][
        "max_position_per_stock"
    ]
    assert payload["risk"]["portfolio_exposure"] <= payload["risk_budget"]["target_exposure"]
    assert payload["risk"]["max_beijing_weight"] == payload["risk_budget"]["max_beijing_weight"]
    assert payload["risk"]["exchange_exposure"].get("BJ", 0) <= payload["risk_budget"][
        "max_beijing_weight"
    ]
    assert "correlation_risk" in payload
    assert "factor_health" in payload
    assert "concentration_risk" in payload
    assert "portfolio_stability" in payload
    assert "backtest" in payload
    assert 0 <= payload["factor_health"]["factor_health_score"] <= 1.05
    assert 0 <= payload["portfolio_stability"]["stability_score"] <= 1
    assert {"cagr", "sharpe", "max_drawdown", "turnover", "win_rate"} <= set(
        payload["backtest"]["metrics"]
    )
    assert payload["backtest"]["equity_curve"]
    assert payload["backtest"]["drawdown_curve"]

    first = payload["data"][0]
    assert {"code", "score", "final_score", "factors", "metrics", "contribution", "reason"} <= set(
        first
    )
    assert {"momentum", "quality", "value", "risk"} <= set(first["factors"])
    assert {"revenue_growth_yoy", "net_profit_growth_yoy", "ocf_to_profit"} <= set(
        first["metrics"]
    )
    assert "factor_health_score" in first
    assert "exchange_risk_multiplier" in first
    assert "liquidity_risk_multiplier" in first

    first_position = payload["portfolio"][0]
    assert {"code", "weight", "score", "final_score"} <= set(first_position)
    assert first_position["weight"] <= payload["risk_budget"]["max_position_per_stock"]
    assert max(payload["risk"]["industry_exposure"].values()) <= payload["risk_budget"][
        "max_industry_weight"
    ]

    first_signal = payload["signals"][0]
    assert {
        "code",
        "action",
        "confidence",
        "position_size",
        "tradability",
        "signal_confidence",
        "reason",
    } <= set(first_signal)
    assert first_signal["action"] in {"BUY", "HOLD", "NO_TRADE"}
    assert 0 <= first_signal["confidence"] <= 1


def test_picks_endpoint_is_deterministic_for_same_input() -> None:
    first = client.get("/api/picks?date=2026-06-24&top_n=5").json()
    second = client.get("/api/picks?date=2026-06-24&top_n=5").json()

    assert first["snapshot_id"] == second["snapshot_id"]
    assert first["data_version"] == second["data_version"]
    assert first["data"] == second["data"]
    assert first["portfolio"] == second["portfolio"]
    assert first["signals"] == second["signals"]
    assert first["signal_summary"] == second["signal_summary"]
    assert first["risk"] == second["risk"]
    assert first["market_regime"] == second["market_regime"]
    assert first["risk_budget"] == second["risk_budget"]
    assert first["correlation_risk"] == second["correlation_risk"]
    assert first["factor_health"] == second["factor_health"]
    assert first["portfolio_stability"] == second["portfolio_stability"]
    assert first["backtest"] == second["backtest"]


def test_portfolio_caps_beijing_exchange_exposure() -> None:
    picks = [
        {"code": "920001.BJ", "final_score": 0.9, "industry": "A"},
        {"code": "920002.BJ", "final_score": 0.8, "industry": "B"},
        {"code": "600001.SH", "final_score": 0.7, "industry": "C"},
        {"code": "000001.SZ", "final_score": 0.6, "industry": "D"},
    ]

    result = build_portfolio(
        picks,
        max_position_per_stock=0.6,
        max_industry_weight=0.8,
        target_exposure=1.0,
        max_beijing_weight=0.15,
    )

    assert result["risk"]["exchange_exposure"]["BJ"] <= 0.15


def test_tradability_blocks_untradeable_candidates() -> None:
    position = {
        "code": "600001.SH",
        "name": "Test",
        "metrics": {
            "latest_pct_chg": 9.9,
            "latest_amount": 10_000,
            "turnover_rate": 0.2,
            "volatility_20d": 0.08,
        },
    }

    result = assess_tradability(position)

    assert result["tradable"] is False
    assert "near limit up" in result["reasons"]
    assert "low latest amount" in result["reasons"]
    assert "low turnover" in result["reasons"]
