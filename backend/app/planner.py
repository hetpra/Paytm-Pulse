"""Business logic — pure functions, no I/O, unit-tested.

Every function takes data in, returns data out. No repo calls here.
"""

from __future__ import annotations
import math
from typing import Optional

from app.config import (
    AT_RISK_BUFFER_DAYS,
    COVER_DAYS,
    LOAN_PROC_FEE_PCT,
    LOAN_RATE_PCT,
    LOAN_ROUNDING,
    LOAN_TENURE_DAYS,
    OPERATING_RESERVE,
    PLATFORM_FEE_PCT,
    PREMIUM_PRICE,
    SAFETY_FACTOR,
)


def status_for(sku: dict, forecast: dict) -> str:
    """Determine SKU restock status: incoming | critical | warning | ok."""
    if sku.get("incoming_qty", 0) > 0:
        return "incoming"
    days_left = forecast.get("days_left", 999)
    lead = sku.get("lead_time_days", 2)
    if days_left <= lead:
        return "critical"
    if days_left <= lead + AT_RISK_BUFFER_DAYS:
        return "warning"
    return "ok"


def reorder_qty(sku: dict, forecast: dict) -> int:
    """
    Reorder quantity: max(0, ceil(sum(yhat[0 : lead + COVER_DAYS]) × SAFETY_FACTOR − current_stock)).
    """
    series = forecast.get("series", [])
    lead = sku.get("lead_time_days", 2)
    window = lead + COVER_DAYS
    yhat_values = [s.get("yhat", 0) for s in series[:window]]
    demand = sum(yhat_values) * SAFETY_FACTOR
    qty = max(0, math.ceil(demand - sku["current_stock"]))
    return qty


def build_plan(at_risk_skus: list[dict], forecasts: dict[str, dict],
               suppliers: dict[str, dict]) -> dict:
    """
    Build line items and POs grouped by supplier.

    Args:
        at_risk_skus: list of SKU dicts (status is critical or warning)
        forecasts: {sku_id: forecast_dict}
        suppliers: {supplier_id: supplier_dict}

    Returns:
        {line_items, purchase_orders, subtotal, platform_fee, total}
    """
    line_items = []
    po_by_supplier: dict[str, dict] = {}  # supplier_id -> {items, subtotal}

    for sku in at_risk_skus:
        fc = forecasts.get(sku["id"], {})
        qty = reorder_qty(sku, fc)
        if qty <= 0:
            continue

        line_total = qty * sku["unit_cost"]
        supplier = suppliers.get(sku["supplier_id"], {})

        item = {
            "sku_id": sku["id"],
            "name": sku["name"],
            "emoji": sku.get("emoji"),
            "qty": qty,
            "unit_cost": sku["unit_cost"],
            "line_total": line_total,
            "supplier_id": sku["supplier_id"],
            "supplier_name": supplier.get("name", ""),
            "days_left": fc.get("days_left", 0),
            "status": status_for(sku, fc),
        }
        line_items.append(item)

        # Group by supplier
        sid = sku["supplier_id"]
        if sid not in po_by_supplier:
            po_by_supplier[sid] = {
                "supplier_id": sid,
                "supplier_name": supplier.get("name", ""),
                "subtotal": 0,
                "items": [],
            }
        po_by_supplier[sid]["subtotal"] += line_total
        po_by_supplier[sid]["items"].append(item)

    # Compute PO fees
    purchase_orders = []
    for po in po_by_supplier.values():
        subtotal = po["subtotal"]
        platform_fee = round(subtotal * PLATFORM_FEE_PCT / 100, 2)
        total = subtotal + platform_fee
        purchase_orders.append({
            "supplier_id": po["supplier_id"],
            "supplier_name": po["supplier_name"],
            "subtotal": subtotal,
            "platform_fee": platform_fee,
            "total": total,
        })

    grand_subtotal = sum(po["subtotal"] for po in purchase_orders)
    grand_fee = sum(po["platform_fee"] for po in purchase_orders)
    grand_total = grand_subtotal + grand_fee

    return {
        "line_items": line_items,
        "purchase_orders": purchase_orders,
        "subtotal": grand_subtotal,
        "platform_fee": grand_fee,
        "total": grand_total,
    }


def cash_check(cash_balance: float, total: float,
               preapproved_limit: float) -> dict:
    """
    Compute cash available, gap, and loan offer.

    Returns {cash_available, cash_gap, loan_offer: {...} | None}.
    """
    cash_available = max(0, cash_balance - OPERATING_RESERVE)
    cash_gap = max(0, total - cash_available)

    if cash_gap == 0:
        return {
            "cash_available": cash_available,
            "cash_gap": 0,
            "loan_offer": None,
        }

    # Loan: principal rounded UP to LOAN_ROUNDING multiple, capped at preapproved limit
    principal = min(
        math.ceil(cash_gap / LOAN_ROUNDING) * LOAN_ROUNDING,
        preapproved_limit,
    )
    interest = principal * LOAN_RATE_PCT / 100
    processing_fee = principal * LOAN_PROC_FEE_PCT / 100
    total_repayment = principal + interest + processing_fee
    fully_covered = principal >= cash_gap

    return {
        "cash_available": cash_available,
        "cash_gap": cash_gap,
        "loan_offer": {
            "principal": principal,
            "interest_rate_pct": LOAN_RATE_PCT,
            "interest": interest,
            "processing_fee": processing_fee,
            "tenure_days": LOAN_TENURE_DAYS,
            "total_repayment": total_repayment,
            "fully_covered": fully_covered,
        },
    }


def revenue_at_risk(skus: list[dict], forecasts: dict[str, dict]) -> float:
    """
    Revenue at risk (7 days) for at-risk SKUs.
    Per SKU = sell_price × max(0, sum(yhat[:7]) − current_stock).
    """
    total = 0
    for sku in skus:
        fc = forecasts.get(sku["id"], {})
        status = status_for(sku, fc)
        if status in ("critical", "warning"):
            series = fc.get("series", [])
            demand_7d = sum(s.get("yhat", 0) for s in series[:7])
            lost = max(0, demand_7d - sku["current_stock"])
            total += sku["sell_price"] * lost
    return round(total, 2)


def revenue_ledger(loans: list[dict], pos: list[dict], plan: str) -> dict:
    """
    Paytm revenue ledger for this demo run.
    Returns {loan_interest, loan_fees, b2b_fees, subscriptions, total, mix_pct}.
    """
    loan_interest = sum(l.get("interest", 0) for l in loans)
    loan_fees = sum(l.get("processing_fee", 0) for l in loans)
    b2b_fees = sum(p.get("platform_fee", 0) for p in pos)
    subscriptions = PREMIUM_PRICE if plan == "premium" else 0

    total = loan_interest + loan_fees + b2b_fees + subscriptions

    mix_pct = {}
    if total > 0:
        mix_pct = {
            "loan": round((loan_interest + loan_fees) / total * 100, 1),
            "b2b": round(b2b_fees / total * 100, 1),
            "subscription": round(subscriptions / total * 100, 1),
        }
    else:
        mix_pct = {"loan": 0, "b2b": 0, "subscription": 0}

    return {
        "loan_interest": loan_interest,
        "loan_fees": loan_fees,
        "b2b_fees": b2b_fees,
        "subscriptions": subscriptions,
        "total": total,
        "mix_pct": mix_pct,
    }
