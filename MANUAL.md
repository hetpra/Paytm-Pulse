# MANUAL.md — Paytm Pulse (Build Guide for AI Coding Agents)

**Team:** Code Review · **Track:** 1 – Merchant Growth AI · **Budget:** 2–3 hours · **Output:** working local demo on synthetic data

---

## 0. How to use this file

**Human (30 seconds):**
1. Put this file in an empty project folder (or attach it to your agent chat).
2. Do the prerequisites in §1 (~10 min; can be done while the agent works).
3. Paste the **Kickoff Prompt** below into any coding agent (Claude Code, Cursor, Codex CLI, Copilot agent, Windsurf…).
4. After each `CHECKPOINT ✅` message, skim the evidence and reply "continue".

**Kickoff Prompt (copy-paste):**

> You are my senior full-stack engineer. Read MANUAL.md completely before writing any code. Follow §2 (Master Prompt) and execute checkpoints CP0 → CP7 in order. After each checkpoint run its Verify steps, show me the evidence, `git commit`, and continue without asking questions unless you are truly blocked. Respect the timeboxes and use the fallbacks in §8. Start with CP0.

**Short-context agents:** paste only §2, §3, the spec sections the current checkpoint references (§4.x), and the current checkpoint from §5.

---

## 1. Human prerequisites (≈10 min, non-blocking)

| Need | Detail |
|---|---|
| Python 3.10–3.12 | Prophet's wheels are most reliable on these |
| Node 18+ | for Vite/React |
| LLM API key (optional) | Anthropic or OpenAI. Without one, alerts use a template and everything still works |
| Supabase project (optional) | Create project → SQL editor → run `backend/schema.sql` (agent writes it in CP1) → copy URL + **service_role** key into `.env`. Without it, the app runs on an in-memory DB |

The agent must **never block** on these. Default config (`DB_MODE=memory`, `LLM_PROVIDER=none`) runs the full demo with zero accounts.

---

## 2. MASTER PROMPT (agent: this is your mission)

**Role:** Senior full-stack + ML engineer shipping a hackathon demo under time pressure.

**Mission:** Build **Paytm Pulse** — a predictive AI copilot for mid-sized Paytm merchants that:
1. Forecasts demand from daily sales and predicts the **exact stockout date** per product (Facebook Prophet).
2. **Auto-drafts purchase orders** to partner wholesale distributors.
3. Detects the **cash-flow gap** for the restock and offers a **one-click, pre-approved Paytm Business Loan**.
4. Executes everything after **ONE merchant approval click** (LangGraph workflow that pauses for approval).
5. Shows the merchant a clean mobile-style dashboard and shows Paytm its revenue (loan interest + fees, 1% B2B fee, ₹499/mo subscription).

**Definition of success:** a 90-second live demo, running locally on synthetic data: dashboard → red Restock Alert → one tap → POs placed + loan disbursed → stock shows "incoming" → Paytm revenue ledger updates.

**Rules (non-negotiable):**
1. **Numbers come from code, words come from the LLM.** The LLM never calculates quantities, prices, dates, or loan terms.
2. **Everything is simulated.** No real payments/loans. Show a visible "Simulated demo" label in the UI.
3. **Work checkpoint by checkpoint.** After each: run Verify → print `CHECKPOINT n ✅` + evidence → `git commit -m "CPn: …"`. Do not start the next checkpoint until Verify passes **or** you applied the listed fallback.
4. **Timebox:** if a checkpoint exceeds 1.5× its budget, apply its 🛟 fallback and move on. Log it in `README.md → Known limitations`.
5. **Don't ask questions** unless blocked. Make a reasonable assumption and record it in `README.md → Assumptions`.
6. **Keep it small:** no Docker, no auth, no Redux, no Next.js, no extra frameworks, no abstractions beyond the `Repo` interface. Prefer boring, readable code.
7. **Contract-first:** the API shapes in §4.5 are frozen. Backend and frontend must both conform exactly.
8. **Resilience:** the demo must survive bad venue Wi-Fi: DB falls back to memory, LLM falls back to a template, Prophet falls back to a seasonal-average forecaster.
9. **No secrets in git.** Use `.env` (gitignored) + `.env.example`.
10. **Final message** must contain: how to run (3 commands), the demo script (§6), assumptions, known limitations.

---

## 3. Frozen decisions (do not re-debate)

| Layer | Choice | Notes |
|---|---|---|
| Forecasting | `prophet` (Facebook Prophet) | weekly seasonality only; fallback forecaster in §4.3 |
| Database | Supabase (Postgres) **or** in-memory | via one `Repo` interface; `DB_MODE=supabase\|memory` (default `memory`) |
| Orchestration | LangGraph | `StateGraph` + `MemorySaver` + `interrupt()` for human approval |
| Backend | FastAPI + Uvicorn | CORS for `http://localhost:5173` |
| LLM | Anthropic or OpenAI behind `llm.py` | `LLM_PROVIDER=anthropic\|openai\|none` (default `none`) |
| Frontend | React (JSX) + Vite + Tailwind CSS + Recharts | mobile-first, centered phone-width column. Install Tailwind per its current official Vite guide |

**Repo layout**
```
paytm-pulse/
├─ MANUAL.md  README.md  .env.example  .gitignore
├─ backend/
│  ├─ requirements.txt  schema.sql
│  ├─ app/  main.py config.py models.py seed.py forecast.py planner.py llm.py graph.py routes.py
│  │        repo/ __init__.py base.py memory_repo.py supabase_repo.py
│  └─ tests/ test_forecast.py test_planner.py test_e2e.py
└─ frontend/
   └─ src/ App.jsx api.js mock/dashboard.json components/{Header,SalesChart,RestockAlert,SkuList,PlanSheet,ForecastChart,RevenueView,Toast}.jsx
```

**`.env.example`**
```
DB_MODE=memory                  # memory | supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=           # service_role key, backend only
LLM_PROVIDER=none               # none | anthropic | openai
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_MODEL=                      # optional override
FORECAST_ENGINE=prophet         # prophet | fallback
MERCHANT_ID=m1
CORS_ORIGINS=http://localhost:5173
```
Frontend: `frontend/.env` → `VITE_API_URL=http://localhost:8000`

**Run commands (must work at the end)**
```
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev
cd backend && pytest -q
```
`requirements.txt`: fastapi, uvicorn[standard], pydantic, python-dotenv, pandas, numpy, prophet, langgraph, supabase, anthropic, openai, pytest, httpx. (Install `prophet` early/in background; it is the slowest.)

**Business constants** — all in `config.py`, nowhere else:

| Constant | Value | Meaning |
|---|---|---|
| `FORECAST_HORIZON` | 21 | days forecast ahead |
| `COVER_DAYS` | 7 | days of stock wanted after an order arrives |
| `SAFETY_FACTOR` | 1.10 | demand buffer |
| `AT_RISK_BUFFER_DAYS` | 3 | warning window beyond lead time |
| `OPERATING_RESERVE` | 1000 | ₹ merchant must keep in cash |
| `PLATFORM_FEE_PCT` | 1.0 | % of PO subtotal (paid by merchant, income for Paytm) |
| `LOAN_RATE_PCT` | 1.5 | flat for the whole tenure |
| `LOAN_PROC_FEE_PCT` | 1.0 | % of principal |
| `LOAN_TENURE_DAYS` | 30 | |
| `LOAN_ROUNDING` | 500 | principal rounded **up** to this multiple |
| `PREMIUM_PRICE` | 499 | ₹/month |

---

## 4. Specs

### 4.1 Database schema (`backend/schema.sql`, Postgres/Supabase)

```sql
create table merchants (
  id text primary key, name text not null, owner_name text,
  cash_balance numeric not null default 0,
  preapproved_limit numeric not null default 0,
  plan text not null default 'free'            -- free | premium
);
create table suppliers (id text primary key, name text not null, city text);
create table skus (
  id text primary key,
  merchant_id text references merchants(id),
  supplier_id text references suppliers(id),
  name text not null, emoji text,
  unit_cost numeric not null, sell_price numeric not null,
  current_stock int not null,
  incoming_qty int not null default 0, incoming_eta date,
  lead_time_days int not null default 2
);
create table daily_sales (
  sku_id text references skus(id), sale_date date not null, units_sold int not null,
  primary key (sku_id, sale_date)
);
create table forecasts (
  sku_id text primary key references skus(id),
  computed_at timestamptz default now(), engine text,
  avg_daily_demand numeric, days_left numeric, stockout_date date,
  series jsonb                                  -- [{date, yhat, lower, upper}] x FORECAST_HORIZON
);
create table proposals (
  id text primary key, merchant_id text references merchants(id), thread_id text,
  status text not null default 'pending',       -- pending | approved | rejected
  alert_text text, payload jsonb not null,      -- full Proposal JSON (§4.5)
  created_at timestamptz default now(), decided_at timestamptz
);
create table purchase_orders (
  id text primary key, proposal_id text references proposals(id),
  merchant_id text, supplier_id text, items jsonb not null,
  subtotal numeric, platform_fee numeric, total numeric,
  status text default 'sent', created_at timestamptz default now()
);
create table loans (
  id text primary key, proposal_id text references proposals(id), merchant_id text,
  principal numeric, interest_rate_pct numeric, interest numeric, processing_fee numeric,
  tenure_days int, total_repayment numeric,
  status text default 'disbursed', created_at timestamptz default now()
);
```

**`Repo` interface** (`repo/base.py`; implement in `memory_repo.py` with plain dicts/lists and `supabase_repo.py` with `supabase-py`):
`get_merchant(id)`, `update_merchant(id, **f)`, `list_suppliers()`, `list_skus(merchant_id)`, `update_sku(id, **f)`, `get_sales(sku_id, days)`, `upsert_forecast(sku_id, data)`, `get_forecasts(merchant_id)`, `create_proposal(d)`, `get_proposal(id)`, `get_pending_proposal(merchant_id)`, `update_proposal(id, **f)`, `create_po(d)`, `list_pos(merchant_id)`, `create_loan(d)`, `list_loans(merchant_id)`, `clear_transactions(merchant_id)`, `bulk_insert_sales(rows)`, plus `seed_base(merchant, suppliers, skus)`. `get_repo()` in `repo/__init__.py` picks by `DB_MODE`; if Supabase init fails, **log a warning and fall back to memory**.

### 4.2 Seed data (`seed.py`, deterministic: `numpy.random.default_rng(42)`)

Merchant: `m1` "Sharma General Store", owner "Ramesh Sharma", `cash_balance=6000`, `preapproved_limit=50000`, `plan=free`.
Suppliers: `s1` "Ganesh FMCG Distributors", `s2` "Annapurna Grocery Wholesale".

| id | name | emoji | unit_cost | sell_price | base/day | stock | lead | supplier |
|---|---|---|---|---|---|---|---|---|
| parle-g | Parle-G Biscuits (₹10) | 🍪 | 8.5 | 10 | 60 | 100 | 2 | s1 |
| maggi | Maggi 2-Min Noodles | 🍜 | 12 | 14 | 45 | 130 | 2 | s1 |
| lays | Lay's Chips (₹20) | 🥔 | 17 | 20 | 30 | 110 | 3 | s1 |
| coke | Coca-Cola 750ml | 🥤 | 36 | 40 | 22 | 400 | 2 | s1 |
| surf | Surf Excel 1kg | 🧺 | 195 | 220 | 3 | 70 | 3 | s1 |
| atta | Aashirvaad Atta 5kg | 🌾 | 245 | 275 | 8 | 30 | 2 | s2 |
| salt | Tata Salt 1kg | 🧂 | 24 | 28 | 12 | 200 | 2 | s2 |
| tea | Red Label Tea 250g | 🍵 | 105 | 120 | 6 | 70 | 3 | s2 |

**Sales history:** 120 days ending yesterday (oldest→newest, `t=0..119`):
`λ = base × dow_factor[weekday] × (1 + 0.002·t)`; `units = max(0, round(rng.normal(λ, 0.12·λ)))`; `dow_factor` Mon..Sun = `[0.90, 0.90, 0.95, 1.00, 1.10, 1.30, 1.15]`. → 960 rows.

**Demo scenario acceptance** (tune `stock` values, *not* the forecaster, until true): ≥1 SKU `critical`; 3–4 SKUs at-risk (`critical`+`warning`); ≥3 SKUs `ok`; proposal total roughly ₹15,000–₹35,000; `cash_gap > 0`; loan `principal ≤ 50000` and `fully_covered = true`. (Expected shape: parle-g ≈1.7 days, maggi ≈2.9, lays ≈3.7, atta ≈3.8; the rest ≥11 days.)

`seed_all()` = base data + sales + forecasts (once per process; ~20 s with Prophet — log progress). `reset_demo_state()` = restore stock/incoming/cash/plan, clear proposals/POs/loans, **keep forecasts** (no refit).

### 4.3 Forecast spec (`forecast.py`)

- Per SKU: dataframe `ds, y` from `daily_sales`. Prophet: `Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False, interval_width=0.8)`; predict next `FORECAST_HORIZON` days (day 1 = tomorrow). Clamp `yhat/lower/upper ≥ 0`. Silence `cmdstanpy`/`prophet` loggers.
- **Fallback forecaster** (`FORECAST_ENGINE=fallback`, or automatically if Prophet import/fit fails): `yhat[d] = mean(units on the same weekday over last 8 weeks) × clamp(mean(last14)/mean(last56), 0.8, 1.2)`; `lower/upper = yhat ∓ 1.28·std`. Same output shape.
- **Stock-out math** — `compute_stockout(stock, yhat[], today)`:
  ```
  cum = cumulative_sum(yhat)
  i = first index with cum[i] >= stock
  if found: days_left = i + (stock - (cum[i-1] if i>0 else 0)) / yhat[i]
  else:     days_left = len(yhat) + (stock - cum[-1]) / mean(yhat)
  stockout_date = today + ceil(days_left) days
  ```
  Test vector: stock 100, constant 60/day → `days_left ≈ 1.667`, `stockout_date = today+2`.
- Persist per SKU: engine, avg_daily_demand (mean of first 7 `yhat`), days_left, stockout_date, series.
- CLI: `python -m app.forecast` prints a table (sku, stock, avg demand, days_left, stockout_date, status, engine).

### 4.4 Business rules (`planner.py` — pure functions, no I/O, unit-tested)

1. **Status:** `incoming_qty > 0` → `incoming` (excluded from planning). Else `critical` if `days_left ≤ lead_time_days`; `warning` if `days_left ≤ lead_time_days + AT_RISK_BUFFER_DAYS`; else `ok`. *At-risk = critical + warning.*
2. **Reorder qty** = `max(0, ceil(sum(yhat[0 : lead_time + COVER_DAYS]) × SAFETY_FACTOR − current_stock))`.
3. **Line total** = `qty × unit_cost`. **Group by supplier** → one PO per supplier. Per PO: `subtotal`, `platform_fee = round(subtotal × 1%, 2)`, `total = subtotal + fee`. Proposal `subtotal/platform_fee/total` = sums over POs.
4. **Cash:** `cash_available = max(0, cash_balance − OPERATING_RESERVE)`; `cash_gap = max(0, total − cash_available)`.
5. **Loan:** if `cash_gap == 0` → `loan_offer = null`. Else `principal = min(ceil(cash_gap/500)×500, preapproved_limit)`; `interest = principal × 1.5%`; `processing_fee = principal × 1%`; `total_repayment = principal + interest + processing_fee`; `fully_covered = principal ≥ cash_gap`.
6. **On approve:** create POs + loan (if any); `cash_balance += principal − total`; for each ordered SKU `incoming_qty = qty`, `incoming_eta = today + lead_time_days`; proposal → `approved`. **On reject:** proposal → `rejected`, nothing else changes.
7. **Revenue at risk (7d)** per at-risk SKU = `sell_price × max(0, sum(yhat[:7]) − current_stock)`; KPI = sum.
8. **Paytm revenue ledger:** `loan_interest = Σ interest`, `loan_fees = Σ processing_fee`, `b2b_fees = Σ PO platform_fee`, `subscriptions = 499 if plan=="premium" else 0`; `total`, and `mix_pct` of each.

**Unit-test vectors (must pass):**
- Constant forecast 60/day, lead 2, stock 100, unit_cost 8.5 → `qty = 494`, `line_total = 4199.0`.
- PO subtotal 10,000 → fee 100, total 10,100. Cash 6,000, reserve 1,000 → available 5,000, gap 5,100 → `principal 5500`, `interest 82.5`, `processing_fee 55`, `total_repayment 5637.5`, `fully_covered true`.
- Cash 20,000, same PO → `loan_offer null`.
- Gap 80,000, limit 50,000 → `principal 50000`, `fully_covered false`.
- SKU with `incoming_qty>0` is excluded from at-risk.

### 4.5 API contract (FROZEN) — base `http://localhost:8000`, JSON, merchant defaults to `m1`

| Method & path | Returns |
|---|---|
| `GET /health` | `{status:"ok", db_mode, llm_mode, forecast_engine, forecasts_ready}` |
| `GET /api/dashboard` | Dashboard (below) |
| `GET /api/skus/{sku_id}/forecast` | `{sku_id, name, history:[{date,units}] (last 30d), forecast:[{date,yhat,lower,upper}], stockout_date, days_left}` |
| `POST /api/analyze` `{merchant_id}` | `{proposal: Proposal \| null}` — runs the graph to the approval pause. Idempotent: returns the existing pending proposal if there is one. `null` if nothing is at risk |
| `GET /api/proposals/{id}` | `Proposal` |
| `POST /api/proposals/{id}/approve` | `{proposal, purchase_orders:[PO], loan: Loan \| null, merchant:{cash_balance}}` |
| `POST /api/proposals/{id}/reject` | `{proposal}` |
| `GET /api/revenue` | `{loan_interest, loan_fees, b2b_fees, subscriptions, total, mix_pct:{loan, b2b, subscription}}` |
| `POST /api/merchant/plan` `{plan:"free"\|"premium"}` | `{merchant}` |
| `POST /api/demo/reset` | `{ok:true}` |

**Dashboard**
```json
{
  "ready": true,
  "merchant": {"id":"m1","name":"Sharma General Store","cash_balance":6000,"preapproved_limit":50000,"plan":"free"},
  "kpis": {"revenue_at_risk_7d": 0, "skus_at_risk": 0, "items_total": 8},
  "sales_last_14d": [{"date":"2026-01-01","revenue":0}],
  "skus": [{"id":"parle-g","name":"…","emoji":"🍪","current_stock":100,"incoming_qty":0,"incoming_eta":null,
            "avg_daily_demand":60.0,"days_left":1.7,"stockout_date":"2026-01-03","status":"critical","stock_pct":0.1}],
  "pending_proposal": null
}
```
`stock_pct` = `min(1, days_left / 14)` (drives the bar). `sales_last_14d.revenue` = Σ units × sell_price per day.

**Proposal**
```json
{
  "id":"prop_ab12cd34","merchant_id":"m1","status":"pending","alert_text":"…","created_at":"…",
  "line_items":[{"sku_id":"parle-g","name":"…","emoji":"🍪","qty":494,"unit_cost":8.5,"line_total":4199.0,
                 "supplier_id":"s1","supplier_name":"…","days_left":1.7,"status":"critical"}],
  "purchase_orders":[{"supplier_id":"s1","supplier_name":"…","subtotal":0,"platform_fee":0,"total":0}],
  "subtotal":0,"platform_fee":0,"total":0,
  "cash_available":5000,"cash_gap":0,
  "loan_offer":{"principal":0,"interest_rate_pct":1.5,"interest":0,"processing_fee":0,"tenure_days":30,
                "total_repayment":0,"fully_covered":true},
  "revenue_at_risk_7d":0
}
```
`Loan` = same fields as `loan_offer` + `id, status:"disbursed"`. `PO` = `{id, supplier_id, supplier_name, items, subtotal, platform_fee, total, status:"sent"}`.

### 4.6 LangGraph workflow (`graph.py`)

```
START → load_and_select ──(none at risk)──▶ END
              │
              ▼
          draft_po → check_cash → write_alert → save_proposal → await_approval → execute → END
```
| Node | Does |
|---|---|
| `load_and_select` | read SKUs + cached forecasts + merchant; compute status; keep at-risk SKUs |
| `draft_po` | planner: qty, line items, POs by supplier, totals |
| `check_cash` | planner: cash_available, gap, loan offer |
| `write_alert` | `llm.generate_alert(facts)` (never raises; falls back to template) |
| `save_proposal` | persist `pending` proposal (+ `thread_id`) via Repo |
| `await_approval` | **only** `decision = interrupt({"proposal_id": …})` — *no side effects in this node* |
| `execute` | if `decision["approved"]`: planner rule 6 (POs, loan, cash, incoming); else mark rejected |

Skeleton (**verify against the installed LangGraph version's docs**: `pip show langgraph`):
```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

class PulseState(TypedDict, total=False):
    merchant_id: str; at_risk: list; plan: dict; cash: dict
    alert_text: str; proposal_id: str; decision: dict; result: dict

def await_approval(state):
    return {"decision": interrupt({"proposal_id": state["proposal_id"]})}

g = StateGraph(PulseState)
# add_node(...) for each node above
g.add_edge(START, "load_and_select")
g.add_conditional_edges("load_and_select", lambda s: "draft_po" if s.get("at_risk") else END)
# add_edge chain: draft_po → check_cash → write_alert → save_proposal → await_approval → execute → END
graph = g.compile(checkpointer=MemorySaver())

# analyze:  graph.invoke({"merchant_id": mid}, {"configurable": {"thread_id": tid}})   # stops at interrupt
# approve:  graph.invoke(Command(resume={"approved": True}),  {"configurable": {"thread_id": tid}})
# reject:   graph.invoke(Command(resume={"approved": False}), {"configurable": {"thread_id": tid}})
```
Use one process-wide `graph` object. Store `thread_id` on the proposal. If the thread is missing on approve (server restarted), execute planner rule 6 directly from the stored proposal payload.

### 4.7 LLM spec (`llm.py`)

`generate_alert(facts: dict, language="en") -> str` — 8 s timeout; **any** failure/`none` → `template_alert(facts)`.

Provider defaults: anthropic → `claude-haiku-4-5-20251001`, openai → `gpt-4o-mini`, override via `LLM_MODEL` (check provider docs if a model name errors).

**System prompt:**
> You are Paytm Pulse, a friendly business copilot for small Indian shopkeepers. Write ONE short alert (max 60 words) in simple English, no jargon, no markdown. Mention the most urgent product and how many days of stock are left, how many items need restocking and the total order value, and — only if loan_offer is present — that a pre-approved Paytm Business Loan of that exact amount can cover the gap. End with: "Approve to place the order." Use ₹. Use ONLY the numbers given in the JSON; never invent or recompute numbers.

**User message:** JSON `{top_item:{name,days_left}, items_at_risk, total, cash_available, loan_offer}`.

**Template fallback:** `⚠️ {top} will run out in ~{ceil(days)} day(s). {n} items need restocking — order ₹{total:,.0f} from {k} distributor(s). You have ₹{avail:,.0f} available; a pre-approved Paytm Business Loan of ₹{principal:,.0f} covers the gap. Approve to place the order.` (omit the loan sentence when there is no gap).

### 4.8 Frontend spec (React + Tailwind, mobile-first, centered `max-w-md` column on a soft background)

Palette: navy `#002E6E`, Paytm blue `#00BAF2`, alert red `#E5322D`, amber `#F5A623`, green `#1FB57A`.

- **Header:** "Inventory", merchant name, cash chip (`₹6,000`), plan badge (FREE / PREMIUM). Tiny "Simulated demo" tag.
- **KPI row:** "₹X revenue at risk this week" · "N items at risk".
- **SalesChart:** 14-day revenue bars (Recharts).
- **RestockAlert card** (only when `pending_proposal`): red ⚠️ icon, **Restock Alert**, the `alert_text`, a summary strip (`N items · Order ₹total · Loan ₹principal @1.5%`), buttons **✕ (reject)** and **✓ Approve & Fund** (one tap = approve; show "Placing orders…" spinner). Tapping the card body opens **PlanSheet** (bottom sheet): line items grouped by supplier, subtotal, 1% fee, total, cash available, cash gap, loan terms (principal, interest, fee, repay-by amount/date).
- **If no pending proposal and some SKUs at risk:** button "Run AI analysis" → `POST /api/analyze`.
- **SkuList:** each row = emoji, name, stock bar (green/amber/red by status, width = `stock_pct`), "≈N days left" (or "Out tomorrow" if ≤1), tap → **ForecastChart** (history + forecast + confidence band + stockout marker). Rows with `incoming_qty>0` show a blue "📦 +qty arriving {eta}" chip. **Premium gate:** ForecastChart is blurred with "Unlock with Premium ₹499/mo" when `plan=free`; a header toggle flips plan via `/api/merchant/plan`.
- **Success state** (after approve): toast/modal "Orders placed with 2 distributors ✓ · Loan ₹19,500 disbursed ✓ · Cash ₹…".
- **RevenueView** ("Paytm view" tab/toggle): this-run revenue from `/api/revenue` (loan interest, loan fees, B2B fees, subscriptions) + pie/stacked bar; caption "Projected mix: 60% loan · 30% B2B · 10% subscriptions".
- **Footer:** small "Reset demo" link → `/api/demo/reset` then refetch.
- Loading skeletons; API errors → toast, never a blank screen. Build against `src/mock/dashboard.json` first (copy of the §4.5 contract) so UI work can start before the backend is done.

---

## 5. Checkpoints

> Total budget ≈ 2h25m + 15 min buffer. After each checkpoint: Verify → `CHECKPOINT n ✅` + evidence → `git commit`.

### CP0 — Scaffold & health (⏱ 10 min)
**Do:** `git init`; folders per §3; `.gitignore` (`.env`, `.venv`, `node_modules`, `__pycache__`); `.env.example`; `config.py` (env + all constants); FastAPI app with CORS and `/health`; Vite React + Tailwind app showing "Paytm Pulse"; start `pip install prophet` in background.
**Verify:** `curl localhost:8000/health` → JSON with `status:"ok"`; `npm run dev` renders the page with Tailwind styling.
**🛟** Tailwind setup stuck >10 min → ship plain CSS for now, retry at CP7.

### CP1 — Data layer & seed (⏱ 15 min) — see §4.1, §4.2
**Do:** `schema.sql`; `Repo` base + `MemoryRepo` + `SupabaseRepo` + `get_repo()` fallback; `seed.py` (`seed_base`, sales generator, `reset_demo_state`).
**Verify:** `python -m app.seed` prints `merchants=1 suppliers=2 skus=8 daily_sales=960`; re-running gives identical numbers (deterministic). If Supabase creds exist: same counts appear in the Supabase tables.
**🛟** Supabase issue >10 min → leave `DB_MODE=memory`, mark "Supabase implemented, untested" in README.

### CP2 — Forecast engine (⏱ 20 min) — see §4.3
**Do:** `forecast.py` (Prophet + fallback + `compute_stockout` + persistence + CLI table); `tests/test_forecast.py` using the 100-stock/60-per-day vector.
**Verify:** `python -m app.forecast` shows 8 SKUs with engine name; satisfies the **demo scenario acceptance** in §4.2 (adjust seed `stock` values if not); `pytest tests/test_forecast.py` green.
**🛟** Prophet install/fit fails or is >5 s per SKU → `FORECAST_ENGINE=fallback`; `/health` must report the engine actually used.

### CP3 — Planner (business logic) (⏱ 10 min) — see §4.4
**Do:** `planner.py` pure functions: `status_for`, `reorder_qty`, `build_plan` (line items + POs + totals), `cash_check` (gap + loan), `revenue_at_risk`, `revenue_ledger`; `tests/test_planner.py` with **all** vectors in §4.4.
**Verify:** `pytest tests/test_planner.py` green.
**🛟** None. This is the heart of the pitch; do not skip tests.

### CP4 — Read API & contract (⏱ 15 min) — see §4.5
**Do:** `routes.py`: `/api/dashboard`, `/api/skus/{id}/forecast`, `/api/revenue`, `/api/merchant/plan`, `/api/demo/reset`; seed + forecast at startup (log progress; `forecasts_ready` flag).
**Verify:** `curl /api/dashboard` has every key in the §4.5 sample, ≥3 at-risk SKUs, `kpis.revenue_at_risk_7d > 0`; `curl /api/skus/parle-g/forecast` returns 30 history + 21 forecast points.
**🛟** None.
**⚡ Parallelizable:** from here, the frontend (CP6 UI work) can start against `mock/dashboard.json` if your agent supports sub-agents.

### CP5 — LangGraph + LLM + approval flow (⏱ 25 min) — see §4.6, §4.7
**Do:** `llm.py`; `graph.py`; `POST /api/analyze`, `GET /api/proposals/{id}`, `/approve`, `/reject`; `tests/test_e2e.py` (FastAPI `TestClient`, `DB_MODE=memory`, `LLM_PROVIDER=none`, `FORECAST_ENGINE=fallback`).
**e2e test asserts:** reset → analyze returns a proposal with ≥3 line items, `loan_offer` present, non-empty `alert_text` → analyze again returns the **same** proposal id → approve returns ≥1 PO and 1 loan → dashboard shows `incoming_qty>0` on ordered SKUs and updated `cash_balance` (`old + principal − total`, and ≥ reserve) → analyze now returns `proposal: null` → `/api/revenue.total > 0` → reset restores the initial state → reject path leaves cash/stock unchanged.
**Verify:** `pytest -q` all green; manual curl run of analyze → approve prints the real numbers; with a real key set, `alert_text` is LLM-written; with `LLM_PROVIDER=none` it uses the template.
**🛟** `interrupt/resume` fights you >15 min → keep LangGraph for `load → draft → cash → alert → save_proposal` (ends there) and make `/approve` call `planner` rule 6 directly from the stored proposal. Note it in README.

### CP6 — Frontend (⏱ 35 min) — see §4.8
**Do:** `api.js` (typed to §4.5), all components in §4.8, success state, loading/error states.
**Verify (manual checklist, report each):** (1) dashboard loads with chart + SKU list; (2) red Restock Alert shows with loan summary; (3) ✓ Approve & Fund → success toast; alert disappears; rows show "📦 arriving"; cash chip updates; (4) ✕ path works after Reset; (5) tapping a SKU shows the forecast chart; (6) Paytm view shows revenue > 0; (7) `npm run build` passes; (8) no console errors; (9) usable at 390 px width.
**🛟** Charts misbehave → show numbers + simple div bars; skip the confidence band.

### CP7 — Demo hardening & docs (⏱ 15 min)
**Do:** run the full demo (§6) twice with Reset between; Premium blur/toggle; "Simulated demo" labels; empty/error states; `README.md` (run steps, architecture sketch, **Assumptions**, **Known limitations**, demo script); final `pytest -q`; `git tag demo-ready`.
**Verify:** a fresh clone + the three run commands works with only `.env.example` copied to `.env` (memory/none/fallback defaults).

### CP8 — Stretch (only if ≥20 min remain; do in this order)
1. Hinglish toggle for alert text (`language="hinglish"` param in `generate_alert`; same numbers).
2. "Why this alert?" sheet (LLM explains in 2 lines using the forecast facts).
3. WhatsApp-style notification preview of the alert.
4. Premium "auto-approve under ₹X" rule shown as a setting (UI only).

---

## 6. Demo script (90 seconds) & claim → proof

1. **Hook (10s):** "Millions of kirana owners lose sales to stockouts and can't afford the reorder." Show dashboard: red KPI "₹X revenue at risk this week".
2. **Predict (15s):** open Parle-G → forecast chart with the stockout marker: "Prophet predicts it runs out on {date}."
3. **Alert (15s):** the Restock Alert card, LLM plain-language message.
4. **One click (20s):** point at the loan summary on the card, tap **✓ Approve & Fund**. LangGraph resumes → POs to 2 distributors + loan disbursed.
5. **Result (10s):** rows flip to "📦 arriving", cash chip updates.
6. **Paytm wins (15s):** "Paytm view": loan interest + fees + 1% B2B fee (+ ₹499 premium unlock).
7. **Close (5s):** "Contextual credit at the exact moment of need — zero-friction."

| Deck claim | Where it's visible | Checkpoint |
|---|---|---|
| Predict exact stockout dates (Prophet) | SKU rows + ForecastChart | CP2, CP6 |
| AI drafts purchase orders | PlanSheet line items by distributor | CP3, CP5 |
| Cash-gap detection + pre-approved loan | Alert card strip + PlanSheet | CP3 |
| One-click approval (LangGraph pause) | ✓ Approve & Fund | CP5, CP6 |
| LLM plain-text alerts | Alert text | CP5 |
| Managed DB (Supabase) | `DB_MODE=supabase` | CP1 |
| Loan interest / 1% B2B / ₹499 premium | Paytm view, Premium blur | CP4, CP6, CP7 |

---

## 7. If you run late — cut in this order
**Must:** CP0–CP5 + minimal UI (alert card, approve, SKU list). **Should:** forecast chart, success state, revenue view. **Could:** Premium blur, Hinglish, extras. Never cut the unit tests in CP3 or the e2e test in CP5.

---

## 8. Fallback ladder

| Problem | Fallback |
|---|---|
| Prophet won't install / is slow | `FORECAST_ENGINE=fallback` (§4.3) |
| Supabase unreachable / not configured | `DB_MODE=memory` (auto-fallback) |
| No LLM key / API error / timeout | template alert (auto-fallback) |
| LangGraph interrupt/resume issues | persisted proposal + direct execute (CP5 🛟) |
| Tailwind config issues | plain CSS, retry later |
| Port conflicts | change `--port` and `VITE_API_URL` / `CORS_ORIGINS` together |
| Demo state gets messy | `POST /api/demo/reset` (no refit, instant) |
| Don't use `uvicorn --reload` during the demo | it re-seeds and re-fits on each reload |

---

## 9. Final deliverables checklist (agent: confirm each in your last message)

- [ ] All CP0–CP7 evidence shown; `pytest -q` green
- [ ] Three run commands work from a fresh clone with default `.env`
- [ ] `/health` reports db / llm / forecast engine actually in use
- [ ] README has Assumptions + Known limitations + demo script
- [ ] "Simulated demo" label visible in UI; no secrets committed

**Assumptions to state in README:** synthetic data and a single merchant; no real Paytm/lending APIs; loan terms (1.5% flat/30 days, 1% fee, ₹50k pre-approved limit) are illustrative; the 1% platform fee is charged to the merchant on top of the PO; the revenue mix on the deck (60/30/10) is a projection, while the in-app ledger shows this demo run's actuals.
