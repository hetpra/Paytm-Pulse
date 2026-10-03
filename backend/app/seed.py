"""Seed data generator — deterministic via numpy.random.default_rng(42)."""

from __future__ import annotations
import logging
import sys
from datetime import date, timedelta

import numpy as np

from app.repo import get_repo

logger = logging.getLogger(__name__)

# ── Base data ───────────────────────────────────────────────────
MERCHANT = {
    "id": "m1",
    "name": "Sharma General Store",
    "owner_name": "Ramesh Sharma",
    "cash_balance": 6000,
    "preapproved_limit": 50000,
    "plan": "free",
}

SUPPLIERS = [
    {"id": "s1", "name": "Ganesh FMCG Distributors", "city": "Mumbai"},
    {"id": "s2", "name": "Annapurna Grocery Wholesale", "city": "Delhi"},
]

SKUS = [
    {"id": "parle-g", "name": "Parle-G Biscuits (₹10)", "emoji": "🍪", "unit_cost": 8.5,  "sell_price": 10,  "base_daily": 60, "current_stock": 100, "lead_time_days": 2, "supplier_id": "s1"},
    {"id": "maggi",   "name": "Maggi 2-Min Noodles",    "emoji": "🍜", "unit_cost": 12,   "sell_price": 14,  "base_daily": 45, "current_stock": 130, "lead_time_days": 2, "supplier_id": "s1"},
    {"id": "lays",    "name": "Lay's Chips (₹20)",      "emoji": "🥔", "unit_cost": 17,   "sell_price": 20,  "base_daily": 30, "current_stock": 110, "lead_time_days": 3, "supplier_id": "s1"},
    {"id": "coke",    "name": "Coca-Cola 750ml",         "emoji": "🥤", "unit_cost": 36,   "sell_price": 40,  "base_daily": 22, "current_stock": 400, "lead_time_days": 2, "supplier_id": "s1"},
    {"id": "surf",    "name": "Surf Excel 1kg",          "emoji": "🧺", "unit_cost": 195,  "sell_price": 220, "base_daily": 3,  "current_stock": 70,  "lead_time_days": 3, "supplier_id": "s1"},
    {"id": "atta",    "name": "Aashirvaad Atta 5kg",     "emoji": "🌾", "unit_cost": 245,  "sell_price": 275, "base_daily": 8,  "current_stock": 30,  "lead_time_days": 2, "supplier_id": "s2"},
    {"id": "salt",    "name": "Tata Salt 1kg",           "emoji": "🧂", "unit_cost": 24,   "sell_price": 28,  "base_daily": 12, "current_stock": 200, "lead_time_days": 2, "supplier_id": "s2"},
    {"id": "tea",     "name": "Red Label Tea 250g",      "emoji": "🍵", "unit_cost": 105,  "sell_price": 120, "base_daily": 6,  "current_stock": 70,  "lead_time_days": 3, "supplier_id": "s2"},
]

# Day-of-week factors: Mon(0)..Sun(6)
DOW_FACTOR = [0.90, 0.90, 0.95, 1.00, 1.10, 1.30, 1.15]


def _generate_sales(rng: np.random.Generator) -> list[dict]:
    """Generate 120 days of sales history ending yesterday."""
    today = date.today()
    rows = []
    for sku in SKUS:
        base = sku["base_daily"]
        for t in range(120):
            day = today - timedelta(days=120 - t)
            weekday = day.weekday()
            lam = base * DOW_FACTOR[weekday] * (1 + 0.002 * t)
            units = max(0, round(rng.normal(lam, 0.12 * lam)))
            rows.append({
                "sku_id": sku["id"],
                "sale_date": day.isoformat(),
                "units_sold": int(units),
            })
    return rows


def seed_base():
    """Seed merchant, suppliers, and SKUs (no sales or forecasts)."""
    repo = get_repo()
    sku_rows = []
    for sku in SKUS:
        row = {
            "id": sku["id"],
            "merchant_id": "m1",
            "supplier_id": sku["supplier_id"],
            "name": sku["name"],
            "emoji": sku["emoji"],
            "unit_cost": sku["unit_cost"],
            "sell_price": sku["sell_price"],
            "current_stock": sku["current_stock"],
            "incoming_qty": 0,
            "incoming_eta": None,
            "lead_time_days": sku["lead_time_days"],
        }
        sku_rows.append(row)
    repo.seed_base(MERCHANT, SUPPLIERS, sku_rows)
    return sku_rows


def seed_sales():
    """Generate and insert 120 days of deterministic sales history."""
    rng = np.random.default_rng(42)
    repo = get_repo()
    rows = _generate_sales(rng)
    repo.bulk_insert_sales(rows)
    return len(rows)


def seed_all():
    """Full seed: base data + sales + forecasts. ~20s with Prophet."""
    logger.info("Seeding base data...")
    seed_base()

    logger.info("Generating sales history (120 days × 8 SKUs)...")
    n_sales = seed_sales()
    logger.info(f"  → {n_sales} sales rows inserted")

    logger.info("Running forecasts...")
    from app.forecast import run_all_forecasts
    run_all_forecasts("m1")

    repo = get_repo()
    m = repo.get_merchant("m1")
    suppliers = repo.list_suppliers()
    skus = repo.list_skus("m1")
    logger.info(f"Seed complete: merchants=1 suppliers={len(suppliers)} skus={len(skus)} daily_sales={n_sales}")
    return {"merchants": 1, "suppliers": len(suppliers), "skus": len(skus), "daily_sales": n_sales}


def reset_demo_state(merchant_id: str = "m1"):
    """Restore stock/incoming/cash/plan, clear proposals/POs/loans. Keep forecasts."""
    repo = get_repo()
    repo.clear_transactions(merchant_id)
    logger.info(f"Demo state reset for {merchant_id}")


# CLI entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = seed_all()
    print(f"\nmerchants={result['merchants']} suppliers={result['suppliers']} "
          f"skus={result['skus']} daily_sales={result['daily_sales']}")
