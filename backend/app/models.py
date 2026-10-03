"""Pydantic models for Paytm Pulse."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


# ── Entities ────────────────────────────────────────────────────
class Merchant(BaseModel):
    id: str
    name: str
    owner_name: Optional[str] = None
    cash_balance: float = 0
    preapproved_limit: float = 0
    plan: str = "free"


class Supplier(BaseModel):
    id: str
    name: str
    city: Optional[str] = None


class Sku(BaseModel):
    id: str
    merchant_id: str
    supplier_id: str
    name: str
    emoji: Optional[str] = None
    unit_cost: float
    sell_price: float
    current_stock: int
    incoming_qty: int = 0
    incoming_eta: Optional[str] = None
    lead_time_days: int = 2


class DailySale(BaseModel):
    sku_id: str
    sale_date: str
    units_sold: int


class Forecast(BaseModel):
    sku_id: str
    computed_at: Optional[str] = None
    engine: Optional[str] = None
    avg_daily_demand: Optional[float] = None
    days_left: Optional[float] = None
    stockout_date: Optional[str] = None
    series: Optional[list] = None


# ── API shapes ──────────────────────────────────────────────────
class LineItem(BaseModel):
    sku_id: str
    name: str
    emoji: Optional[str] = None
    qty: int
    unit_cost: float
    line_total: float
    supplier_id: str
    supplier_name: str
    days_left: float
    status: str


class PurchaseOrderSummary(BaseModel):
    supplier_id: str
    supplier_name: str
    subtotal: float
    platform_fee: float
    total: float


class LoanOffer(BaseModel):
    principal: float
    interest_rate_pct: float = 1.5
    interest: float
    processing_fee: float
    tenure_days: int = 30
    total_repayment: float
    fully_covered: bool


class Proposal(BaseModel):
    id: str
    merchant_id: str
    status: str = "pending"
    alert_text: Optional[str] = None
    created_at: Optional[str] = None
    line_items: list[LineItem] = []
    purchase_orders: list[PurchaseOrderSummary] = []
    subtotal: float = 0
    platform_fee: float = 0
    total: float = 0
    cash_available: float = 0
    cash_gap: float = 0
    loan_offer: Optional[LoanOffer] = None
    revenue_at_risk_7d: float = 0


class SkuDashboard(BaseModel):
    id: str
    name: str
    emoji: Optional[str] = None
    current_stock: int
    incoming_qty: int = 0
    incoming_eta: Optional[str] = None
    avg_daily_demand: float = 0
    days_left: float = 0
    stockout_date: Optional[str] = None
    status: str = "ok"
    stock_pct: float = 0


class KPIs(BaseModel):
    revenue_at_risk_7d: float = 0
    skus_at_risk: int = 0
    items_total: int = 0


class Dashboard(BaseModel):
    ready: bool
    merchant: Merchant
    kpis: KPIs
    sales_last_14d: list[dict] = []
    skus: list[SkuDashboard] = []
    pending_proposal: Optional[Proposal] = None
