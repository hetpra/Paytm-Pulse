# Paytm Pulse

**Predictive AI copilot for mid-sized Paytm merchants** — forecasts demand, predicts stockout dates, auto-drafts purchase orders, detects cash-flow gaps, and offers one-click pre-approved Paytm Business Loans.

> ⚠️ **Simulated demo** — All data is synthetic, no real payments or loans are processed.

---

## Quick Start (3 commands)

```bash
# 1. Backend
cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --port 8000

# 2. Frontend (new terminal)
cd frontend && npm install && npm run dev

# 3. Tests (new terminal)
cd backend && .venv\Scripts\activate && pytest -q
```

Copy `.env.example` → `.env` before starting. Default config (`DB_MODE=memory`, `LLM_PROVIDER=none`, `FORECAST_ENGINE=prophet`) runs the full demo with zero external accounts.

**Frontend:** http://localhost:5173 &nbsp;|&nbsp; **Backend:** http://localhost:8000 &nbsp;|&nbsp; **Health:** http://localhost:8000/health

---

## Architecture

```
┌──────────────┐     REST API      ┌──────────────────────────────────────┐
│  React/Vite  │ ◄───────────────► │        FastAPI + Uvicorn             │
│  Tailwind    │   localhost:8000   │                                      │
│  Recharts    │                    │  ┌──────────┐  ┌─────────────────┐  │
│              │                    │  │ Prophet / │  │  LangGraph      │  │
│  localhost:  │                    │  │ Fallback  │  │  (interrupt/    │  │
│    5173      │                    │  │ Forecast  │  │   resume for    │  │
│              │                    │  └──────────┘  │   approval)     │  │
└──────────────┘                    │                 └─────────────────┘  │
                                    │  ┌──────────────────────────────┐    │
                                    │  │ Repo (Memory / Supabase)    │    │
                                    │  └──────────────────────────────┘    │
                                    │  ┌──────────────────────────────┐    │
                                    │  │ LLM (OpenRouter / template) │    │
                                    │  └──────────────────────────────┘    │
                                    └──────────────────────────────────────┘
```

### Key Components

| Module | Purpose |
|---|---|
| `seed.py` | Deterministic data generation (RNG 42), 8 SKUs, 120 days of sales |
| `forecast.py` | Prophet + fallback seasonal forecaster, stockout math |
| `planner.py` | Pure business logic — status, reorder qty, POs, cash gap, loan offer |
| `graph.py` | LangGraph workflow with `interrupt()` for human approval |
| `llm.py` | Alert generation via OpenRouter/Anthropic/OpenAI with template fallback |
| `routes.py` | Frozen API contract (§4.5) |
| `repo/` | Data access via `Repo` interface (Memory or Supabase) |

---

## Demo Script (90 seconds)

1. **Hook (10s):** "Millions of kirana owners lose sales to stockouts." Dashboard shows red KPI "₹X revenue at risk this week."
2. **Predict (15s):** Tap Parle-G → forecast chart with stockout marker. "Prophet predicts it runs out on {date}."
3. **Alert (15s):** Restock Alert card with AI-generated plain-language message.
4. **One click (20s):** Point at loan summary, tap **✓ Approve & Fund**. LangGraph resumes → POs to 2 distributors + loan disbursed.
5. **Result (10s):** Rows flip to "📦 arriving", cash chip updates.
6. **Paytm wins (15s):** "Paytm view" tab: loan interest + fees + 1% B2B fee (+ ₹499 premium unlock).
7. **Close (5s):** "Contextual credit at the exact moment of need — zero-friction."

---

## Configuration

| Variable | Default | Options |
|---|---|---|
| `DB_MODE` | `memory` | `memory`, `supabase` |
| `LLM_PROVIDER` | `none` | `none`, `openrouter`, `anthropic`, `openai` |
| `FORECAST_ENGINE` | `prophet` | `prophet`, `fallback` |
| `OPENROUTER_API_KEY` | — | Your OpenRouter key |
| `LLM_MODEL` | auto | e.g. `google/gemini-2.0-flash-001` |
| `SUPABASE_URL` | — | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | — | Service role key |

---

## Assumptions

- Synthetic data and a single merchant (`m1` — Sharma General Store)
- No real Paytm/lending APIs; all transactions are simulated
- Loan terms (1.5% flat / 30 days, 1% processing fee, ₹50,000 pre-approved limit) are illustrative
- The 1% platform fee is charged to the merchant on top of the PO subtotal
- The revenue mix on the deck (60/30/10) is a projection, while the in-app ledger shows this demo run's actuals
- Prophet with weekly seasonality only; no yearly/daily seasonality
- Day-of-week demand factors: Mon-Tue 0.90, Wed 0.95, Thu 1.00, Fri 1.10, Sat 1.30, Sun 1.15

---

## Known Limitations

- Single-process, single-merchant demo
- In-memory DB resets on server restart (use Supabase for persistence)
- LangGraph `interrupt/resume` may lose thread state on server restart (falls back to direct execution from stored proposal)
- Prophet's plotly dependency not installed (interactive plots unavailable — not needed for demo)
- Frontend chunk size > 500 kB (acceptable for demo; would code-split in production)

---

## Fallback Ladder

| Problem | Fallback |
|---|---|
| Prophet won't install / is slow | `FORECAST_ENGINE=fallback` |
| Supabase unreachable | `DB_MODE=memory` (auto-fallback) |
| No LLM key / API error | Template alert (auto-fallback) |
| LangGraph interrupt issues | Stored proposal + direct execute |
| Port conflicts | Change `--port` and `VITE_API_URL` / `CORS_ORIGINS` |
| Demo state gets messy | `POST /api/demo/reset` |