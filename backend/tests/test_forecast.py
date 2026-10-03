"""Unit tests for forecast.py — stockout math."""

import pytest
from datetime import date
from app.forecast import compute_stockout


class TestComputeStockout:
    def test_constant_60_stock_100(self):
        """Stock 100, constant 60/day → days_left ≈ 1.667, stockout_date = today+2."""
        today = date(2026, 1, 1)
        yhat = [60.0] * 21
        days_left, stockout_date = compute_stockout(100, yhat, today)
        assert abs(days_left - 1.667) < 0.01
        assert stockout_date == date(2026, 1, 3)  # today + 2 days

    def test_stock_exceeds_horizon(self):
        """Stock larger than total forecast → days_left > horizon."""
        today = date(2026, 1, 1)
        yhat = [10.0] * 21
        days_left, stockout_date = compute_stockout(500, yhat, today)
        assert days_left > 21

    def test_zero_stock(self):
        """Zero stock → days_left ≈ 0."""
        today = date(2026, 1, 1)
        yhat = [60.0] * 21
        days_left, stockout_date = compute_stockout(0, yhat, today)
        assert days_left == 0.0
        assert stockout_date == today
