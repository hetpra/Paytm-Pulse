"""E0 guard: core responses are additive and extension-safe."""
import os

os.environ["DB_MODE"] = "memory"
os.environ["LLM_PROVIDER"] = "none"
os.environ["FORECAST_ENGINE"] = "fallback"

from fastapi.testclient import TestClient

from app.main import create_app
from app.repo import reset_repo


def test_core_contracts_are_present(monkeypatch):
    monkeypatch.setenv("EXT_ENABLED", "none")
    reset_repo()
    with TestClient(create_app()) as client:
        dashboard = client.get("/api/dashboard").json()
        assert {"ready", "merchant", "kpis", "sales_last_14d", "skus", "pending_proposal"} <= dashboard.keys()
        assert {"revenue_at_risk_7d", "skus_at_risk", "items_total"} <= dashboard["kpis"].keys()
        forecast = client.get("/api/skus/parle-g/forecast").json()
        assert {"sku_id", "name", "history", "forecast", "stockout_date", "days_left"} <= forecast.keys()
        assert {"enabled", "available"} <= client.get("/api/features").json().keys()
    reset_repo()
