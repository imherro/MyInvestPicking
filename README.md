# MyInvestPicking

MyInvestPicking is a FastAPI-based A-share stock-picking workbench. It scans an
A-share universe and returns a reproducible Top 20 candidate list for a future
daily "next-day heavy position" workflow.

## Run

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8019
```

Then open:

```text
http://localhost:8019
```

## Current Scope

- Web UI at `/`
- Stock picks API at `/api/picks`
- Tushare data loading with automatic mock fallback
- Basic universe filtering, factor calculation, and scoring
- Project structure for future strategy and risk modules

## Environment

Create a local `.env` file when using Tushare:

```text
TUSHARE_TOKEN=your-token-here
```

If no token is available, the system uses stable mock data so the web UI,
API, and tests still run.

## API

```text
GET /api/picks
GET /api/picks?date=2026-06-24&top_n=20
```

Response fields include `date`, `source`, `mock_mode`, `universe_size`, and
structured stock picks with `score`, normalized factor scores, and raw metrics.
