"""API routes — all endpoints per MANUAL §4.5 frozen contract."""

from __future__ import annotations
import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repo import get_repo
from app import planner
from app.config import AT_RISK_BUFFER_DAYS

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request models ──────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    merchant_id: str = "m1"

class PlanRequest(BaseModel):
    plan: str  # "free" | "premium"


# ── Dashboard ───────────────────────────────────────────────────
@router.get("/api/dashboard")
def dashboard():
    from app.main import forecasts_ready
    repo = get_repo()
    merchant = repo.get_merchant("m1")
    if not merchant:
        raise HTTPException(404, "Merchant not found")

    skus = repo.list_skus("m1")
    forecasts_list = repo.get_forecasts("m1")
    forecasts = {f["sku_id"]: f for f in forecasts_list}

    # Build SKU dashboard items
    sku_items = []
    at_risk_count = 0
    for sku in skus:
        fc = forecasts.get(sku["id"], {})
        days_left = fc.get("days_left", 999)
        status = planner.status_for(sku, fc)
        if status in ("critical", "warning"):
            at_risk_count += 1
        stock_pct = min(1, days_left / 14) if days_left < float("inf") else 1.0

        sku_items.append({
            "id": sku["id"],
            "name": sku["name"],
            "emoji": sku.get("emoji"),
            "current_stock": sku["current_stock"],
            "incoming_qty": sku.get("incoming_qty", 0),
            "incoming_eta": sku.get("incoming_eta"),
            "avg_daily_demand": fc.get("avg_daily_demand", 0),
            "days_left": round(days_left, 1),
            "stockout_date": fc.get("stockout_date"),
            "status": status,
            "stock_pct": round(stock_pct, 2),
        })

    # Sort: critical first, then warning, then ok
    status_order = {"critical": 0, "warning": 1, "incoming": 2, "ok": 3}
    sku_items.sort(key=lambda x: (status_order.get(x["status"], 9), x.get("days_left", 999)))

    # Revenue at risk
    rev_at_risk = planner.revenue_at_risk(skus, forecasts)

    # Sales last 14 days
    sales_14d = _sales_last_14d(skus)

    # Pending proposal
    pending = repo.get_pending_proposal("m1")
    pending_payload = None
    if pending:
        payload = pending.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload)
        pending_payload = payload

    return {
        "ready": forecasts_ready,
        "merchant": merchant,
        "kpis": {
            "revenue_at_risk_7d": rev_at_risk,
            "skus_at_risk": at_risk_count,
            "items_total": len(skus),
        },
        "sales_last_14d": sales_14d,
        "skus": sku_items,
        "pending_proposal": pending_payload,
    }


def _sales_last_14d(skus: list[dict]) -> list[dict]:
    """Aggregate revenue per day for the last 14 days."""
    repo = get_repo()
    today = date.today()
    day_revenue: dict[str, float] = {}

    for d in range(14):
        day = (today - timedelta(days=13 - d)).isoformat()
        day_revenue[day] = 0

    for sku in skus:
        sales = repo.get_sales(sku["id"], days=14)
        for s in sales:
            d = s["sale_date"]
            if d in day_revenue:
                day_revenue[d] += s["units_sold"] * sku["sell_price"]

    return [{"date": d, "revenue": round(r, 2)} for d, r in sorted(day_revenue.items())]


# ── Forecast detail ─────────────────────────────────────────────
@router.get("/api/skus/{sku_id}/forecast")
def sku_forecast(sku_id: str):
    repo = get_repo()
    skus = repo.list_skus("m1")
    sku = next((s for s in skus if s["id"] == sku_id), None)
    if not sku:
        raise HTTPException(404, "SKU not found")

    forecasts = repo.get_forecasts("m1")
    fc = next((f for f in forecasts if f["sku_id"] == sku_id), None)

    # History: last 30 days
    sales = repo.get_sales(sku_id, days=30)
    history = [{"date": s["sale_date"], "units": s["units_sold"]} for s in sales]

    forecast_series = []
    stockout_date = None
    days_left = None
    if fc:
        forecast_series = fc.get("series", [])
        stockout_date = fc.get("stockout_date")
        days_left = fc.get("days_left")

    return {
        "sku_id": sku_id,
        "name": sku["name"],
        "history": history,
        "forecast": forecast_series,
        "stockout_date": stockout_date,
        "days_left": days_left,
    }


# ── Analyze (run graph) ────────────────────────────────────────
@router.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    from app.graph import run_analyze
    proposal = run_analyze(req.merchant_id)
    return {"proposal": proposal}


# ── Proposal detail ─────────────────────────────────────────────
@router.get("/api/proposals/{proposal_id}")
def get_proposal(proposal_id: str):
    repo = get_repo()
    proposal = repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(404, "Proposal not found")
    payload = proposal.get("payload", {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


# ── Approve ─────────────────────────────────────────────────────
@router.post("/api/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str):
    from app.graph import run_approve
    try:
        result = run_approve(proposal_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


# ── Reject ──────────────────────────────────────────────────────
@router.post("/api/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str):
    from app.graph import run_reject
    try:
        result = run_reject(proposal_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


# ── Revenue ledger ──────────────────────────────────────────────
@router.get("/api/revenue")
def revenue():
    repo = get_repo()
    merchant = repo.get_merchant("m1")
    loans = repo.list_loans("m1")
    pos = repo.list_pos("m1")
    plan = merchant.get("plan", "free") if merchant else "free"
    return planner.revenue_ledger(loans, pos, plan)


# ── Merchant plan toggle ───────────────────────────────────────
@router.post("/api/merchant/plan")
def update_plan(req: PlanRequest):
    repo = get_repo()
    merchant = repo.update_merchant("m1", plan=req.plan)
    return {"merchant": merchant}


# ── Demo reset ──────────────────────────────────────────────────
@router.post("/api/demo/reset")
def demo_reset():
    from app.seed import reset_demo_state
    reset_demo_state("m1")
    return {"ok": True}
