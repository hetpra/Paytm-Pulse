"""Computed growth insights; intentionally independent of other extensions."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache

from fastapi import APIRouter

from app.repo import get_repo

FLAG = "insights"
router = APIRouter()


def _sales(sku_id: str, days: int) -> list[dict]:
    return get_repo().get_sales(sku_id, days=days)


def _revenue(rows: list[dict], price: float) -> float:
    return sum(row["units_sold"] * price for row in rows)


def compute_insights(merchant_id: str = "m1") -> list[dict]:
    repo = get_repo()
    skus = repo.list_skus(merchant_id)
    today = date.today()
    insights: list[dict] = []
    movers_up, movers_down, profits, margins, units = [], [], [], [], []
    weekday_revenue = {day: [] for day in range(7)}
    total_inventory = 0.0
    total_revenue_30 = 0.0
    for sku in skus:
        rows30 = _sales(sku["id"], 30)
        last7 = [r for r in rows30 if r["sale_date"] >= (today - timedelta(days=7)).isoformat()]
        prev7 = [r for r in rows30 if (today - timedelta(days=14)).isoformat() <= r["sale_date"] < (today - timedelta(days=7)).isoformat()]
        last14 = [r for r in rows30 if r["sale_date"] >= (today - timedelta(days=14)).isoformat()]
        rev_last, rev_prev = _revenue(last7, sku["sell_price"]), _revenue(prev7, sku["sell_price"])
        if rev_prev >= 500:
            change = (rev_last - rev_prev) / rev_prev * 100
            if abs(change) >= 10:
                (movers_up if change > 0 else movers_down).append((abs(change), sku, change))
        units14 = sum(r["units_sold"] for r in last14)
        avg14 = units14 / 14
        if sku["current_stock"] > 0 and units14 == 0:
            insights.append(_item("dead_stock", "high", sku, "No sales in 14 days", "Move it with a bundle or discount."))
        elif avg14 and sku["current_stock"] / avg14 >= 21:
            days = round(sku["current_stock"] / avg14)
            insights.append(_item("overstock", "medium", sku, f"~{days} days of stock", f"Pause reordering {sku['name']}."))
        profit = _revenue(rows30, sku["sell_price"] - sku["unit_cost"])
        profits.append((profit, sku))
        total_revenue_30 += _revenue(rows30, sku["sell_price"])
        margins.append(((sku["sell_price"] - sku["unit_cost"]) / sku["sell_price"], sku))
        units.append((sum(r["units_sold"] for r in rows30), sku))
        total_inventory += sku["current_stock"] * sku["unit_cost"]
        for row in rows30:
            weekday_revenue[datetime.fromisoformat(row["sale_date"]).weekday()].append(row["units_sold"] * sku["sell_price"])
    for _, sku, change in sorted(movers_up, reverse=True)[:2]:
        insights.append(_item("mover_up", "medium", sku, f"+{change:.0f}% revenue vs last week", "Keep this item visible and in stock."))
    for _, sku, change in sorted(movers_down, reverse=True)[:2]:
        insights.append(_item("mover_down", "medium", sku, f"{change:.0f}% revenue vs last week", "Check pricing and shelf placement."))
    if any(weekday_revenue.values()):
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        averages = {day: sum(values) / max(1, len(values)) for day, values in weekday_revenue.items()}
        best, worst = max(averages, key=averages.get), min(averages, key=averages.get)
        insights.extend([
            {"type":"best_weekday", "severity":"low", "title":f"{names[best]} is your strongest day", "metric":f"₹{averages[best]:,.0f} average revenue", "evidence":{"weekday": names[best]}, "action":f"Stock up before {names[best]}."},
            {"type":"worst_weekday", "severity":"low", "title":f"{names[worst]} needs attention", "metric":f"₹{averages[worst]:,.0f} average revenue", "evidence":{"weekday": names[worst]}, "action":f"Run a promo on {names[worst]}."},
        ])
    total_profit = sum(value for value, _ in profits)
    for profit, sku in sorted(profits, reverse=True)[:3]:
        share = 100 * profit / total_profit if total_profit else 0
        insights.append(_item("profit_leader", "low", sku, f"₹{profit:,.0f} gross profit ({share:.0f}%)", "Protect availability of this profitable item."))
    margin_cut = sorted(value for value, _ in margins)[len(margins) // 2] if margins else 0
    units_cut = sorted(value for value, _ in units)[len(units) // 2] if units else 0
    for margin, sku in margins:
        sku_units = next(value for value, item in units if item["id"] == sku["id"])
        if margin >= margin_cut and sku_units <= units_cut:
            insights.append(_item("hidden_gem", "low", sku, f"₹{sku['sell_price'] - sku['unit_cost']:.0f}/unit margin", f"Promote {sku['name']}.") )
            break
    if total_revenue_30:
        insights.append({"type":"cash_tied_up", "severity":"low", "title":"Cash tied up in inventory", "metric":f"₹{total_inventory:,.0f}", "evidence":{"inventory_value":round(total_inventory), "revenue_30d":round(total_revenue_30)}, "action":"Use slow-stock promotions to release working capital."})
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(insights, key=lambda item: (rank[item["severity"]], -_metric_value(item["metric"])))[:8]


def _metric_value(value: str) -> float:
    import re
    match = re.search(r"[\d,]+", value)
    return float(match.group().replace(",", "")) if match else 0


def _item(kind: str, severity: str, sku: dict, metric: str, action: str) -> dict:
    return {"type":kind, "severity":severity, "title":sku["name"], "metric":metric, "evidence":{"sku_id":sku["id"]}, "action":action}


def _digest(insights: list[dict]) -> str:
    # Template-only by design: this extension remains fast, offline, and its
    # displayed metrics always have a direct computational source.
    return " ".join(f"{item['title']}: {item['metric']}. {item['action']}" for item in insights[:3])


@router.get("/")
def insights(merchant_id: str = "m1"):
    cards = compute_insights(merchant_id)
    return {"generated_at": datetime.now().isoformat(), "summary_text": _digest(cards), "insights": cards}


def setup(app) -> None:
    return None
