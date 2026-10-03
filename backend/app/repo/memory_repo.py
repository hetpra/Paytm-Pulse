"""In-memory repository implementation using plain dicts/lists."""

from __future__ import annotations
import copy
from datetime import date, datetime, timedelta
from typing import Optional

from app.repo.base import BaseRepo


class MemoryRepo(BaseRepo):
    """Thread-safe-enough for a single-process demo."""

    def __init__(self):
        self.merchants: dict[str, dict] = {}
        self.suppliers: dict[str, dict] = {}
        self.skus: dict[str, dict] = {}
        self.sales: list[dict] = []  # [{sku_id, sale_date, units_sold}]
        self.forecasts: dict[str, dict] = {}  # keyed by sku_id
        self.proposals: dict[str, dict] = {}
        self.purchase_orders: dict[str, dict] = {}
        self.loans: dict[str, dict] = {}
        # Snapshot for reset
        self._base_skus: dict[str, dict] = {}
        self._base_merchant: dict[str, dict] = {}

    # ── Merchants ───────────────────────────────────────────────
    def get_merchant(self, id: str) -> Optional[dict]:
        m = self.merchants.get(id)
        return copy.deepcopy(m) if m else None

    def update_merchant(self, id: str, **fields) -> dict:
        m = self.merchants[id]
        m.update(fields)
        return copy.deepcopy(m)

    # ── Suppliers ───────────────────────────────────────────────
    def list_suppliers(self) -> list[dict]:
        return list(self.suppliers.values())

    # ── SKUs ────────────────────────────────────────────────────
    def list_skus(self, merchant_id: str) -> list[dict]:
        return [copy.deepcopy(s) for s in self.skus.values() if s["merchant_id"] == merchant_id]

    def update_sku(self, id: str, **fields) -> dict:
        s = self.skus[id]
        s.update(fields)
        return copy.deepcopy(s)

    # ── Sales ───────────────────────────────────────────────────
    def get_sales(self, sku_id: str, days: int) -> list[dict]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return sorted(
            [s for s in self.sales if s["sku_id"] == sku_id and s["sale_date"] >= cutoff],
            key=lambda s: s["sale_date"],
        )

    def bulk_insert_sales(self, rows: list[dict]) -> None:
        self.sales.extend(rows)

    # ── Forecasts ───────────────────────────────────────────────
    def upsert_forecast(self, sku_id: str, data: dict) -> None:
        self.forecasts[sku_id] = {**data, "sku_id": sku_id}

    def get_forecasts(self, merchant_id: str) -> list[dict]:
        sku_ids = {s["id"] for s in self.skus.values() if s["merchant_id"] == merchant_id}
        return [copy.deepcopy(self.forecasts[sid]) for sid in sku_ids if sid in self.forecasts]

    # ── Proposals ───────────────────────────────────────────────
    def create_proposal(self, d: dict) -> dict:
        self.proposals[d["id"]] = copy.deepcopy(d)
        return copy.deepcopy(d)

    def get_proposal(self, id: str) -> Optional[dict]:
        p = self.proposals.get(id)
        return copy.deepcopy(p) if p else None

    def get_pending_proposal(self, merchant_id: str) -> Optional[dict]:
        for p in self.proposals.values():
            if p["merchant_id"] == merchant_id and p["status"] == "pending":
                return copy.deepcopy(p)
        return None

    def update_proposal(self, id: str, **fields) -> dict:
        p = self.proposals[id]
        p.update(fields)
        return copy.deepcopy(p)

    # ── Purchase Orders ─────────────────────────────────────────
    def create_po(self, d: dict) -> dict:
        self.purchase_orders[d["id"]] = copy.deepcopy(d)
        return copy.deepcopy(d)

    def list_pos(self, merchant_id: str) -> list[dict]:
        return [copy.deepcopy(p) for p in self.purchase_orders.values() if p.get("merchant_id") == merchant_id]

    # ── Loans ───────────────────────────────────────────────────
    def create_loan(self, d: dict) -> dict:
        self.loans[d["id"]] = copy.deepcopy(d)
        return copy.deepcopy(d)

    def list_loans(self, merchant_id: str) -> list[dict]:
        return [copy.deepcopy(l) for l in self.loans.values() if l.get("merchant_id") == merchant_id]

    # ── Lifecycle ───────────────────────────────────────────────
    def clear_transactions(self, merchant_id: str) -> None:
        """Clear proposals, POs, loans. Keep forecasts and sales."""
        self.proposals = {k: v for k, v in self.proposals.items() if v.get("merchant_id") != merchant_id}
        self.purchase_orders = {k: v for k, v in self.purchase_orders.items() if v.get("merchant_id") != merchant_id}
        self.loans = {k: v for k, v in self.loans.items() if v.get("merchant_id") != merchant_id}
        # Restore SKU stock / incoming / merchant cash from snapshot
        if merchant_id in self._base_merchant:
            self.merchants[merchant_id] = copy.deepcopy(self._base_merchant[merchant_id])
        for sku_id, base in self._base_skus.items():
            if base["merchant_id"] == merchant_id:
                self.skus[sku_id] = copy.deepcopy(base)

    def seed_base(self, merchant: dict, suppliers: list[dict], skus: list[dict]) -> None:
        self.merchants[merchant["id"]] = copy.deepcopy(merchant)
        self._base_merchant[merchant["id"]] = copy.deepcopy(merchant)
        for s in suppliers:
            self.suppliers[s["id"]] = copy.deepcopy(s)
        for sk in skus:
            self.skus[sk["id"]] = copy.deepcopy(sk)
            self._base_skus[sk["id"]] = copy.deepcopy(sk)

    def delete_merchant_data(self, merchant_id: str) -> None:
        sku_ids = {sid for sid, sku in self.skus.items() if sku["merchant_id"] == merchant_id}
        self.sales = [row for row in self.sales if row["sku_id"] not in sku_ids]
        for sid in sku_ids:
            self.skus.pop(sid, None); self.forecasts.pop(sid, None); self._base_skus.pop(sid, None)
        self.merchants.pop(merchant_id, None); self._base_merchant.pop(merchant_id, None)
        self.clear_transactions(merchant_id)
