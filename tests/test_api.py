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
    assert len(payload["data"]) == 5

    first = payload["data"][0]
    assert {"code", "score", "factors", "metrics"} <= set(first)
    assert {"momentum", "quality", "value", "risk"} <= set(first["factors"])
