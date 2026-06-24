# MyInvestPicking

MyInvestPicking is a FastAPI-based A-share stock-picking workbench. The first
version provides only the web/API scaffold for a future daily "next-day heavy
position" candidate workflow.

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
- Placeholder stock picks API at `/api/picks`
- Project structure for future data, factor, strategy, and risk modules

No stock-selection logic is implemented yet.
