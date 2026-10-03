"""Deterministic no-look-ahead comparison of reactive and Pulse ordering."""
from __future__ import annotations

import math
from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.config import AT_RISK_BUFFER_DAYS, COVER_DAYS, SAFETY_FACTOR
from app.repo import get_repo

FLAG = "impact"
router = APIRouter()
SIM_CASH_AVAILABLE = 5000.0


def simulate(merchant_id: str = "m1", days: int = 30) -> dict:
    repo = get_repo()
    skus = repo.list_skus(merchant_id)
    today, start = date.today(), date.today() - timedelta(days=days)
    totals = {"without":{"lost_units":0, "lost_revenue":0.0, "lost_profit":0.0, "stockout_days":0}, "with":{"lost_units":0, "lost_revenue":0.0, "lost_profit":0.0, "stockout_days":0}}
    costs = {"platform_fees":0.0, "loan_costs":0.0}
    daily = [{"date":(start + timedelta(days=i)).isoformat(), "lost_without_cum":0.0, "lost_with_cum":0.0} for i in range(days)]
    by_sku = []
    for sku in skus:
        rows = repo.get_sales(sku["id"], 120)
        by_day = {r["sale_date"]: r["units_sold"] for r in rows}
        prior = [r["units_sold"] for r in rows if r["sale_date"] < start.isoformat()][-28:]
        starting = round(7 * (sum(prior) / len(prior) if prior else 0))
        result = _simulate_sku(sku, by_day, start, days, starting)
        for policy in ("without", "with"):
            for key in totals[policy]: totals[policy][key] += result[policy][key]
        costs["platform_fees"] += result["platform_fees"]; costs["loan_costs"] += result["loan_costs"]
        for index, (wo, wp) in enumerate(zip(result["daily_without"], result["daily_with"])):
            daily[index]["lost_without_cum"] += wo; daily[index]["lost_with_cum"] += wp
        by_sku.append({"sku_id":sku["id"], "name":sku["name"], "lost_without":result["without"]["lost_revenue"], "lost_with":result["with"]["lost_revenue"]})
    for item in daily:
        item["lost_without_cum"] = round(item["lost_without_cum"], 2); item["lost_with_cum"] = round(item["lost_with_cum"], 2)
    for policy in totals.values():
        for key, value in policy.items(): policy[key] = round(value, 2)
    revenue_protected = totals["without"]["lost_revenue"] - totals["with"]["lost_revenue"]
    net_gain = totals["without"]["lost_profit"] - totals["with"]["lost_profit"] - costs["platform_fees"] - costs["loan_costs"]
    return {"window":{"days":days, "start":start.isoformat(), "end":(today-timedelta(days=1)).isoformat()}, "assumptions":{"starting_stock":"7 × prior 28-day average", "reactive_arrival":"lead + 1 days", "pulse_arrival":"lead days", "cash_available":SIM_CASH_AVAILABLE, "platform_fee_pct":1, "loan_cost_pct":2.5}, "without":totals["without"], "with":totals["with"], "costs":{key:round(value,2) for key,value in costs.items()}, "revenue_protected":round(revenue_protected,2), "net_gain":round(net_gain,2), "daily":daily, "by_sku":by_sku}


def _simulate_sku(sku, demand, start, days, initial):
    def run(pulse):
        stock, pending, lost, pending_value = initial, [], [], 0.0
        stat = {"lost_units":0, "lost_revenue":0.0, "lost_profit":0.0, "stockout_days":0}
        fees = loan = 0.0
        trailing = []
        for i in range(days):
            day = start + timedelta(days=i); key = day.isoformat()
            arriving = sum(q for eta, q in pending if eta == i); pending = [(eta,q) for eta,q in pending if eta != i]
            stock += arriving
            qty_demand = demand.get(key, 0); sold = min(stock, qty_demand); missed = qty_demand - sold; stock -= sold
            stat["lost_units"] += missed; stat["lost_revenue"] += missed * sku["sell_price"]; stat["lost_profit"] += missed * (sku["sell_price"]-sku["unit_cost"]); stat["stockout_days"] += int(missed > 0); lost.append(stat["lost_revenue"])
            history = trailing[-28:] or [qty_demand]; avg = sum(history) / len(history) if history else 0
            has_pending = bool(pending)
            should_order = pulse and avg and stock / avg <= sku["lead_time_days"] + AT_RISK_BUFFER_DAYS and not has_pending
            should_order = should_order or (not pulse and stock == 0 and not has_pending and avg > 0)
            if should_order:
                order = math.ceil(((sku["lead_time_days"] + COVER_DAYS) * avg * SAFETY_FACTOR - stock) if pulse else 7 * avg)
                order = max(0, order); eta = i + (sku["lead_time_days"] if pulse else sku["lead_time_days"] + 1); pending.append((eta, order))
                if pulse:
                    value = order * sku["unit_cost"]; fees += value * .01
                    if value > SIM_CASH_AVAILABLE: loan += (value-SIM_CASH_AVAILABLE) * .025
            trailing.append(qty_demand)
        return stat, lost, fees, loan
    wo, daily_wo, _, _ = run(False); wp, daily_wp, fee, loan = run(True)
    return {"without":wo, "with":wp, "daily_without":daily_wo, "daily_with":daily_wp, "platform_fees":fee, "loan_costs":loan}


@router.get("/")
def impact(merchant_id: str = "m1", days: int = Query(30, ge=14, le=60)):
    return simulate(merchant_id, days)


def setup(app) -> None:
    return None
