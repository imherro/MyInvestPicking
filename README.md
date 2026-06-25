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
- Unified API catalog at `/api`
- Stock picks API at `/api/picks`
- Shadow portfolio history API at `/api/shadow-portfolio`
- Tushare data loading with automatic mock fallback
- Trading-day normalization and local data caching
- Reproducible snapshot metadata for each stock-picking run
- Basic universe filtering, factor calculation, and scoring
- Score-weighted portfolio construction with position and industry caps
- Drawdown guard and portfolio risk metrics
- Market regime detection with dynamic risk budgets
- Correlation risk, factor health, and portfolio stability metrics
- Deterministic backtest and execution simulation metrics
- Growth/trend scoring mode with separate value, growth, and trend candidate pools
- Project structure for future strategy and risk modules

## Environment

Create a local `.env` file when using Tushare:

```text
TUSHARE_TOKEN=your-token-here
```

If no token is available, the system uses stable mock data so the web UI,
API, and tests still run.

## API

Start from the read-only catalog:

```text
GET /api
```

The catalog returns system metadata, `base_url`, documentation links, recommended
entry points, safety boundaries, functional endpoint groups, and
`total_endpoints`. It is intentionally descriptive only: it does not trigger
stock-picking recomputation, backtests, local cache refreshes, snapshots,
trading, or GitHub synchronization.

```text
GET /api/picks
GET /api/picks?date=2026-06-24&top_n=20
GET /api/picks?shadow_days=0
GET /api/shadow-portfolio?shadow_days=5
```

Response fields include `trading_date`, `data_version`, `factor_version`,
`universe_hash`, `snapshot_id`, `source`, `mock_mode`, `universe_size`, and
structured stock picks with `score`, normalized factor scores, weighted
contributions, raw metrics, and a short reason list. `score_profile` describes
the active growth/trend scoring weights, and `candidate_pools` separates value,
growth, and trend candidates before risk gates are applied. The response also includes
`portfolio` positions with ratio-only `weight` values and a `risk` summary.
Market state is exposed through `market_regime` and `risk_budget`, allowing
position and exposure limits to adapt to trend, range, crash, or high-volatility
conditions.
Risk structure fields include `correlation_risk`, `concentration_risk`,
`factor_health`, and `portfolio_stability`.
The `backtest` block contains a deterministic daily-rebalanced NAV simulation,
drawdown curve, and performance metrics using explicit transaction-cost and
slippage assumptions.

`GET /api/shadow-portfolio` returns the shadow portfolio summary, NAV curve,
rebalance history, and simulation metrics for recent daily model picks.

Documentation is also available at:

```text
GET /docs
GET /redoc
GET /openapi.json
```

Safety boundaries:

- `/api` is catalog-only and does not recompute or write runtime data.
- Analysis endpoints do not place orders, connect to broker accounts, or sync
  external systems.
- Position and exposure outputs remain ratio-only.
- Analysis endpoints may refresh local Tushare cache files or runtime snapshots;
  those files remain under ignored runtime directories.
- The catalog does not expose `.env`, `TUSHARE_TOKEN`, local cache paths, or
  machine-specific absolute paths.

## Runtime Data

The app may create local runtime files under:

```text
data/cache/
data/frozen/
```

These directories are ignored by Git. They hold cached Tushare responses and
deterministic run snapshots.
