"""End-to-end API tests using FastAPI TestClient.

Uses DB_MODE=memory, LLM_PROVIDER=none, FORECAST_ENGINE=fallback.
"""

import os
import pytest

# Force test config BEFORE any app imports
os.environ["DB_MODE"] = "memory"
os.environ["LLM_PROVIDER"] = "none"
os.environ["FORECAST_ENGINE"] = "fallback"

from fastapi.testclient import TestClient
from app.repo import reset_repo


@pytest.fixture(autouse=True)
def fresh_repo():
    """Reset the repo singleton before each test."""
    reset_repo()
    yield
    reset_repo()


@pytest.fixture
def client():
    # Re-import to pick up fresh config
    from app.main import app
    with TestClient(app) as c:
        yield c


class TestEndToEnd:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["forecast_engine"] == "fallback"

    def test_full_flow(self, client):
        """Reset → analyze → analyze again (idempotent) → approve → verify → revenue → reset → reject."""

        # 1. Reset
        r = client.post("/api/demo/reset")
        assert r.status_code == 200

        # 2. Dashboard should load
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        dash = r.json()
        assert dash["ready"] is True
        assert len(dash["skus"]) == 8
        assert dash["kpis"]["skus_at_risk"] > 0

        # 3. Analyze — should return a proposal with ≥3 line items
        r = client.post("/api/analyze", json={"merchant_id": "m1"})
        assert r.status_code == 200
        data = r.json()
        proposal = data["proposal"]
        assert proposal is not None
        assert len(proposal["line_items"]) >= 3
        assert proposal["loan_offer"] is not None
        assert proposal["alert_text"]  # non-empty
        proposal_id = proposal["id"]

        # 4. Analyze again — same proposal id (idempotent)
        r = client.post("/api/analyze", json={"merchant_id": "m1"})
        assert r.json()["proposal"]["id"] == proposal_id

        # 5. Get proposal by id
        r = client.get(f"/api/proposals/{proposal_id}")
        assert r.status_code == 200
        assert r.json()["id"] == proposal_id

        # 6. Approve
        r = client.post(f"/api/proposals/{proposal_id}/approve")
        assert r.status_code == 200
        result = r.json()
        assert len(result.get("purchase_orders", [])) >= 1
        assert result.get("loan") is not None
        merchant = result.get("merchant", {})
        # Cash should be updated: old + principal - total, and >= reserve
        assert merchant.get("cash_balance", 0) >= 1000  # >= OPERATING_RESERVE

        # 7. Dashboard should show incoming
        r = client.get("/api/dashboard")
        dash = r.json()
        incoming_skus = [s for s in dash["skus"] if s["incoming_qty"] > 0]
        assert len(incoming_skus) > 0

        # 8. Analyze now returns null (nothing pending, incoming SKUs excluded)
        r = client.post("/api/analyze", json={"merchant_id": "m1"})
        # May return null or a new smaller proposal
        # (depends on remaining at-risk after incoming exclusion)

        # 9. Revenue should be > 0
        r = client.get("/api/revenue")
        rev = r.json()
        assert rev["total"] > 0

        # 10. Reset restores initial state
        r = client.post("/api/demo/reset")
        assert r.status_code == 200

        r = client.get("/api/dashboard")
        dash = r.json()
        assert dash["merchant"]["cash_balance"] == 6000
        # No incoming after reset
        incoming_after = [s for s in dash["skus"] if s["incoming_qty"] > 0]
        assert len(incoming_after) == 0

    def test_reject_flow(self, client):
        """Reject leaves cash/stock unchanged."""
        # Get initial state
        r = client.get("/api/dashboard")
        initial_cash = r.json()["merchant"]["cash_balance"]

        # Analyze
        r = client.post("/api/analyze", json={"merchant_id": "m1"})
        proposal = r.json()["proposal"]
        proposal_id = proposal["id"]

        # Reject
        r = client.post(f"/api/proposals/{proposal_id}/reject")
        assert r.status_code == 200

        # Cash unchanged
        r = client.get("/api/dashboard")
        assert r.json()["merchant"]["cash_balance"] == initial_cash

        # No incoming
        incoming = [s for s in r.json()["skus"] if s["incoming_qty"] > 0]
        assert len(incoming) == 0

    def test_forecast_detail(self, client):
        """Forecast detail returns history + forecast."""
        r = client.get("/api/skus/parle-g/forecast")
        assert r.status_code == 200
        data = r.json()
        assert data["sku_id"] == "parle-g"
        assert len(data["history"]) > 0
        assert len(data["forecast"]) == 21

    def test_plan_toggle(self, client):
        """Toggle merchant plan."""
        r = client.post("/api/merchant/plan", json={"plan": "premium"})
        assert r.status_code == 200
        assert r.json()["merchant"]["plan"] == "premium"

        r = client.post("/api/merchant/plan", json={"plan": "free"})
        assert r.json()["merchant"]["plan"] == "free"
