from datetime import date

from app.ext.backtest import festival_uplift, metrics
from tests.ext.conftest import client_for


def test_wape_vector():
    assert metrics([10, 20], [12, 18]) == {"wape": 0.1333, "accuracy": 0.8667}


def test_backtest_endpoint_and_uplift_skip():
    points = [{"date": "2026-01-01", "yhat": 100, "lower": 100, "upper": 100}]
    assert festival_uplift(points, today=date(2026, 1, 1), backtest=True) == points
    with client_for("backtest") as client:
        payload = client.get("/api/ext/backtest/").json()
    assert payload["ready"] is True and len(payload["skus"]) == 8
