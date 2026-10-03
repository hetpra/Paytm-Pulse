"""Cash-flow based lending eligibility and illustrative repayment terms."""
from __future__ import annotations

import math
from statistics import mean, pstdev

from fastapi import APIRouter

from app.ext import hooks
from app.ext.store import get_table
from app.repo import get_repo

FLAG = "lending"
router = APIRouter()


def floor_500(value: float) -> int:
    return max(0, int(value // 500) * 500)


def eligibility(merchant: dict) -> dict:
    repo = get_repo(); sku_ids = [sku["id"] for sku in repo.list_skus(merchant["id"])]
    skus = {sku["id"]: sku for sku in repo.list_skus(merchant["id"])}
    rows = [(row, skus[sid]) for sid in sku_ids for row in repo.get_sales(sid, 90)]
    dates = {row["sale_date"] for row, _ in rows}
    if len(dates) < 60:
        return {"limit": 0, "reasons": ["Need at least 60 days of sales"], "avg_daily_revenue": 0}
    daily: dict[str, float] = {}
    for row, sku in rows: daily[row["sale_date"]] = daily.get(row["sale_date"], 0) + row["units_sold"] * sku["sell_price"]
    ordered = [daily[d] for d in sorted(daily)]
    monthly = sum(ordered[-90:]) / 3
    weekly = [sum(ordered[i:i + 7]) for i in range(0, len(ordered) - 6, 7)]
    cv = pstdev(weekly) / mean(weekly) if len(weekly) > 1 and mean(weekly) else 1
    multiplier = 1.0 if cv < .15 else .8 if cv < .30 else .6
    reasons = [f"₹{monthly:,.0f} average monthly revenue", f"Revenue consistency multiplier {multiplier:.1f}"]
    if len(ordered) >= 60:
        prior, recent = sum(ordered[-60:-30]), sum(ordered[-30:])
        if prior and recent / prior - 1 < -.15:
            multiplier *= .8; reasons.append("Recent revenue trend reduced the limit")
    limit = min(200000, floor_500(.25 * monthly * multiplier))
    if limit < 5000:
        reasons.append("Calculated limit is below ₹5,000")
        limit = 0
    return {"limit": limit, "reasons": reasons, "avg_daily_revenue": sum(ordered[-90:]) / max(1, len(ordered)), "monthly_revenue": monthly}


def lending_limit(_limit: float, *, merchant: dict, **_) -> float:
    return eligibility(merchant)["limit"]


def lending_offer(offer: dict | None, *, gap: float, total: float, merchant: dict, **_) -> dict | None:
    if not offer:
        return offer
    facts = eligibility(merchant); limit, avg = facts["limit"], facts["avg_daily_revenue"]
    if limit < 500:
        return None
    principal = min(math.ceil(gap / 500) * 500, limit)
    fully_covered = principal >= gap
    tenure = next((term for term in (30, 45, 60) if principal * (1 + .015 * term / 30 + .01) / term <= .15 * avg), None)
    if tenure is None:
        tenure = 60
        principal = min(principal, floor_500(.15 * avg * tenure / (1 + .03 + .01)))
        fully_covered = False
    interest = principal * .015 * tenure / 30; fee = principal * .01; repayment = principal + interest + fee
    return {"principal": principal, "interest_rate_pct": 1.5, "interest": round(interest, 2), "processing_fee": round(fee, 2), "tenure_days": tenure, "total_repayment": round(repayment, 2), "fully_covered": fully_covered, "daily_deduction": round(repayment / tenure, 2), "share_of_daily_sales_pct": round(repayment / tenure / avg * 100, 2) if avg else 0, "apr_pct": round((interest + fee) / principal * 365 / tenure * 100, 1) if principal else 0, "eligibility":{"limit":limit, "reasons":facts["reasons"]}}


def persist_terms(*, proposal: dict, loan: dict | None = None, **_) -> None:
    payload = proposal.get("payload", {})
    if isinstance(payload, str):
        import json; payload = json.loads(payload)
    terms = payload.get("loan_offer")
    if terms: get_table("loan_terms").insert({"id":proposal["id"], "proposal_id":proposal["id"], "merchant_id":proposal["merchant_id"], "terms":terms})


def setup(app) -> None:
    hooks.register_filter("lending.limit", lending_limit)
    hooks.register_filter("lending.offer", lending_offer)
    hooks.register_event("proposal.approved", persist_terms)
