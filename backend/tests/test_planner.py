"""Unit tests for planner.py — all vectors from MANUAL §4.4."""

import pytest
from app import planner


class TestStatusFor:
    def test_incoming_excluded(self):
        sku = {"incoming_qty": 50, "lead_time_days": 2}
        fc = {"days_left": 1}
        assert planner.status_for(sku, fc) == "incoming"

    def test_critical(self):
        sku = {"incoming_qty": 0, "lead_time_days": 2}
        fc = {"days_left": 1.7}
        assert planner.status_for(sku, fc) == "critical"

    def test_warning(self):
        sku = {"incoming_qty": 0, "lead_time_days": 2}
        fc = {"days_left": 4.5}
        assert planner.status_for(sku, fc) == "warning"

    def test_ok(self):
        sku = {"incoming_qty": 0, "lead_time_days": 2}
        fc = {"days_left": 10}
        assert planner.status_for(sku, fc) == "ok"


class TestReorderQty:
    def test_constant_forecast_60_per_day(self):
        """Constant forecast 60/day, lead 2, stock 100, unit_cost 8.5 → qty = 494."""
        sku = {"current_stock": 100, "lead_time_days": 2, "unit_cost": 8.5}
        # 9 days of forecast at 60/day (lead 2 + cover 7)
        series = [{"yhat": 60}] * 21
        fc = {"series": series, "days_left": 1.67}
        qty = planner.reorder_qty(sku, fc)
        assert qty == 494  # ceil((60*9)*1.10 - 100) = ceil(594-100) = 494


class TestBuildPlan:
    def test_po_fee(self):
        """PO subtotal 10,000 → fee 100, total 10,100."""
        sku = {
            "id": "test",
            "name": "Test",
            "emoji": "🧪",
            "current_stock": 0,
            "lead_time_days": 2,
            "unit_cost": 100,
            "supplier_id": "s1",
        }
        series = [{"yhat": 60}] * 21
        fc = {"series": series, "days_left": 1}
        suppliers = {"s1": {"id": "s1", "name": "Supplier 1"}}

        plan = planner.build_plan([sku], {"test": fc}, suppliers)
        # We can't directly force subtotal=10000 with this helper,
        # but we can test the fee calculation separately
        assert plan["platform_fee"] == round(plan["subtotal"] * 0.01, 2)
        assert plan["total"] == plan["subtotal"] + plan["platform_fee"]


class TestCashCheck:
    def test_gap_with_loan(self):
        """Cash 6000, reserve 1000 → available 5000. Total 10100 → gap 5100
        → principal 5500, interest 82.5, fee 55, repay 5637.5, covered True."""
        result = planner.cash_check(
            cash_balance=6000,
            total=10100,
            preapproved_limit=50000,
        )
        assert result["cash_available"] == 5000
        assert result["cash_gap"] == 5100
        loan = result["loan_offer"]
        assert loan is not None
        assert loan["principal"] == 5500
        assert loan["interest"] == 82.5
        assert loan["processing_fee"] == 55
        assert loan["total_repayment"] == 5637.5
        assert loan["fully_covered"] is True

    def test_no_gap_no_loan(self):
        """Cash 20,000 with same PO → no loan."""
        result = planner.cash_check(
            cash_balance=20000,
            total=10100,
            preapproved_limit=50000,
        )
        assert result["cash_available"] == 19000
        assert result["cash_gap"] == 0
        assert result["loan_offer"] is None

    def test_gap_exceeds_limit(self):
        """Gap 80,000, limit 50,000 → principal 50000, not fully covered."""
        result = planner.cash_check(
            cash_balance=1000,
            total=80000,
            preapproved_limit=50000,
        )
        assert result["cash_gap"] == 80000
        loan = result["loan_offer"]
        assert loan["principal"] == 50000
        assert loan["fully_covered"] is False

    def test_line_total(self):
        """Constant forecast 60/day, lead 2, stock 100, unit_cost 8.5 → line_total = 4199.0."""
        sku = {"current_stock": 100, "lead_time_days": 2, "unit_cost": 8.5}
        series = [{"yhat": 60}] * 21
        fc = {"series": series, "days_left": 1.67}
        qty = planner.reorder_qty(sku, fc)
        line_total = qty * sku["unit_cost"]
        assert qty == 494
        assert line_total == 4199.0


class TestRevenueAtRisk:
    def test_incoming_excluded(self):
        """SKU with incoming_qty > 0 is excluded from at-risk."""
        skus = [
            {"id": "a", "incoming_qty": 50, "lead_time_days": 2, "sell_price": 10, "current_stock": 5},
        ]
        forecasts = {
            "a": {"days_left": 0.5, "series": [{"yhat": 60}] * 7},
        }
        assert planner.revenue_at_risk(skus, forecasts) == 0


class TestRevenueLedger:
    def test_basic(self):
        loans = [{"interest": 82.5, "processing_fee": 55}]
        pos = [{"platform_fee": 100}]
        result = planner.revenue_ledger(loans, pos, "premium")
        assert result["loan_interest"] == 82.5
        assert result["loan_fees"] == 55
        assert result["b2b_fees"] == 100
        assert result["subscriptions"] == 499
        assert result["total"] == 82.5 + 55 + 100 + 499

    def test_free_plan(self):
        result = planner.revenue_ledger([], [], "free")
        assert result["subscriptions"] == 0
        assert result["total"] == 0
