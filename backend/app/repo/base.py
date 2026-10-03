"""Repo interface — abstract base for data access."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseRepo(ABC):
    """Abstract repository interface. All data access goes through this."""

    # ── Merchants ───────────────────────────────────────────────
    @abstractmethod
    def get_merchant(self, id: str) -> Optional[dict]: ...

    @abstractmethod
    def update_merchant(self, id: str, **fields) -> dict: ...

    # ── Suppliers ───────────────────────────────────────────────
    @abstractmethod
    def list_suppliers(self) -> list[dict]: ...

    # ── SKUs ────────────────────────────────────────────────────
    @abstractmethod
    def list_skus(self, merchant_id: str) -> list[dict]: ...

    @abstractmethod
    def update_sku(self, id: str, **fields) -> dict: ...

    # ── Sales ───────────────────────────────────────────────────
    @abstractmethod
    def get_sales(self, sku_id: str, days: int) -> list[dict]: ...

    @abstractmethod
    def bulk_insert_sales(self, rows: list[dict]) -> None: ...

    # ── Forecasts ───────────────────────────────────────────────
    @abstractmethod
    def upsert_forecast(self, sku_id: str, data: dict) -> None: ...

    @abstractmethod
    def get_forecasts(self, merchant_id: str) -> list[dict]: ...

    # ── Proposals ───────────────────────────────────────────────
    @abstractmethod
    def create_proposal(self, d: dict) -> dict: ...

    @abstractmethod
    def get_proposal(self, id: str) -> Optional[dict]: ...

    @abstractmethod
    def get_pending_proposal(self, merchant_id: str) -> Optional[dict]: ...

    @abstractmethod
    def update_proposal(self, id: str, **fields) -> dict: ...

    # ── Purchase Orders ─────────────────────────────────────────
    @abstractmethod
    def create_po(self, d: dict) -> dict: ...

    @abstractmethod
    def list_pos(self, merchant_id: str) -> list[dict]: ...

    # ── Loans ───────────────────────────────────────────────────
    @abstractmethod
    def create_loan(self, d: dict) -> dict: ...

    @abstractmethod
    def list_loans(self, merchant_id: str) -> list[dict]: ...

    # ── Lifecycle ───────────────────────────────────────────────
    @abstractmethod
    def clear_transactions(self, merchant_id: str) -> None: ...

    @abstractmethod
    def seed_base(self, merchant: dict, suppliers: list[dict], skus: list[dict]) -> None: ...

    @abstractmethod
    def delete_merchant_data(self, merchant_id: str) -> None: ...
