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

    first = payload["data"][0]
    assert {"code", "score", "factors", "metrics", "contribution", "reason"} <= set(first)
    assert {"momentum", "quality", "value", "risk"} <= set(first["factors"])
    assert {"revenue_growth_yoy", "net_profit_growth_yoy", "ocf_to_profit"} <= set(
        first["metrics"]
    )


def test_picks_endpoint_is_deterministic_for_same_input() -> None:
    first = client.get("/api/picks?date=2026-06-24&top_n=5").json()
    second = client.get("/api/picks?date=2026-06-24&top_n=5").json()

    assert first["snapshot_id"] == second["snapshot_id"]
    assert first["data_version"] == second["data_version"]
    assert first["data"] == second["data"]
