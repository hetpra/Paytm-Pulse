"""Supabase repository implementation."""

from __future__ import annotations
import json
import copy
import logging
from datetime import date, timedelta
from typing import Optional

from app.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class SupabaseRepo(BaseRepo):
    """Repository backed by Supabase (Postgres via REST)."""

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.client = create_client(url, key)

    # ── Merchants ───────────────────────────────────────────────
    def get_merchant(self, id: str) -> Optional[dict]:
        r = self.client.table("merchants").select("*").eq("id", id).execute()
        return r.data[0] if r.data else None

    def update_merchant(self, id: str, **fields) -> dict:
        r = self.client.table("merchants").update(fields).eq("id", id).execute()
        return r.data[0]

    # ── Suppliers ───────────────────────────────────────────────
    def list_suppliers(self) -> list[dict]:
        return self.client.table("suppliers").select("*").execute().data

    # ── SKUs ────────────────────────────────────────────────────
    def list_skus(self, merchant_id: str) -> list[dict]:
        return self.client.table("skus").select("*").eq("merchant_id", merchant_id).execute().data

    def update_sku(self, id: str, **fields) -> dict:
        r = self.client.table("skus").update(fields).eq("id", id).execute()
        return r.data[0]

    # ── Sales ───────────────────────────────────────────────────
    def get_sales(self, sku_id: str, days: int) -> list[dict]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return (
            self.client.table("daily_sales")
            .select("*")
            .eq("sku_id", sku_id)
            .gte("sale_date", cutoff)
            .order("sale_date")
            .execute()
            .data
        )

    def bulk_insert_sales(self, rows: list[dict]) -> None:
        # Supabase has a row limit per request; batch in chunks of 500
        for i in range(0, len(rows), 500):
            self.client.table("daily_sales").upsert(rows[i : i + 500]).execute()

    # ── Forecasts ───────────────────────────────────────────────
    def upsert_forecast(self, sku_id: str, data: dict) -> None:
        row = {**data, "sku_id": sku_id}
        # Ensure series is JSON-serializable
        if "series" in row and not isinstance(row["series"], str):
            row["series"] = json.dumps(row["series"]) if row["series"] else None
        self.client.table("forecasts").upsert(row).execute()

    def get_forecasts(self, merchant_id: str) -> list[dict]:
        # Join through skus to filter by merchant
        skus = self.list_skus(merchant_id)
        sku_ids = [s["id"] for s in skus]
        if not sku_ids:
            return []
        result = []
        for sid in sku_ids:
            r = self.client.table("forecasts").select("*").eq("sku_id", sid).execute()
            if r.data:
                row = r.data[0]
                if isinstance(row.get("series"), str):
                    row["series"] = json.loads(row["series"])
                result.append(row)
        return result

    # ── Proposals ───────────────────────────────────────────────
    def create_proposal(self, d: dict) -> dict:
        row = copy.deepcopy(d)
        if "payload" in row and not isinstance(row["payload"], str):
            row["payload"] = json.dumps(row["payload"])
        r = self.client.table("proposals").insert(row).execute()
        return r.data[0]

    def get_proposal(self, id: str) -> Optional[dict]:
        r = self.client.table("proposals").select("*").eq("id", id).execute()
        if not r.data:
            return None
        row = r.data[0]
        if isinstance(row.get("payload"), str):
            row["payload"] = json.loads(row["payload"])
        return row

    def get_pending_proposal(self, merchant_id: str) -> Optional[dict]:
        r = (
            self.client.table("proposals")
            .select("*")
            .eq("merchant_id", merchant_id)
            .eq("status", "pending")
            .limit(1)
            .execute()
        )
        if not r.data:
            return None
        row = r.data[0]
        if isinstance(row.get("payload"), str):
            row["payload"] = json.loads(row["payload"])
        return row

    def update_proposal(self, id: str, **fields) -> dict:
        if "payload" in fields and not isinstance(fields["payload"], str):
            fields["payload"] = json.dumps(fields["payload"])
        r = self.client.table("proposals").update(fields).eq("id", id).execute()
        return r.data[0]

    # ── Purchase Orders ─────────────────────────────────────────
    def create_po(self, d: dict) -> dict:
        row = copy.deepcopy(d)
        if "items" in row and not isinstance(row["items"], str):
            row["items"] = json.dumps(row["items"])
        r = self.client.table("purchase_orders").insert(row).execute()
        return r.data[0]

    def list_pos(self, merchant_id: str) -> list[dict]:
        rows = self.client.table("purchase_orders").select("*").eq("merchant_id", merchant_id).execute().data
        for row in rows:
            if isinstance(row.get("items"), str):
                row["items"] = json.loads(row["items"])
        return rows

    # ── Loans ───────────────────────────────────────────────────
    def create_loan(self, d: dict) -> dict:
        r = self.client.table("loans").insert(d).execute()
        return r.data[0]

    def list_loans(self, merchant_id: str) -> list[dict]:
        return self.client.table("loans").select("*").eq("merchant_id", merchant_id).execute().data

    # ── Lifecycle ───────────────────────────────────────────────
    def clear_transactions(self, merchant_id: str) -> None:
        """Clear proposals, POs, loans. Keep forecasts and sales."""
        # Delete in dependency order
        self.client.table("loans").delete().eq("merchant_id", merchant_id).execute()
        self.client.table("purchase_orders").delete().eq("merchant_id", merchant_id).execute()
        self.client.table("proposals").delete().eq("merchant_id", merchant_id).execute()

    def seed_base(self, merchant: dict, suppliers: list[dict], skus: list[dict]) -> None:
        self.client.table("merchants").upsert(merchant).execute()
        for s in suppliers:
            self.client.table("suppliers").upsert(s).execute()
        for sk in skus:
            self.client.table("skus").upsert(sk).execute()

    def delete_merchant_data(self, merchant_id: str) -> None:
        skus = self.list_skus(merchant_id)
        self.clear_transactions(merchant_id)
        for sku in skus:
            self.client.table("forecasts").delete().eq("sku_id", sku["id"]).execute()
            self.client.table("daily_sales").delete().eq("sku_id", sku["id"]).execute()
        self.client.table("skus").delete().eq("merchant_id", merchant_id).execute()
        self.client.table("merchants").delete().eq("id", merchant_id).execute()
