from tests.ext.conftest import client_for


def test_distributor_tracks_delivery_once():
    with client_for("distributor") as client:
        proposal = client.post("/api/analyze", json={"merchant_id":"m1"}).json()["proposal"]
        result = client.post(f"/api/proposals/{proposal['id']}/approve").json()
        po = result["purchase_orders"][0]
        before = client.get("/api/dashboard").json()["skus"]
        for _ in range(3): client.post(f"/api/ext/distributor/pos/{po['id']}/advance")
        final = client.post(f"/api/ext/distributor/pos/{po['id']}/advance").json()["tracking"]
    assert final["status"] == "delivered" and final["delivered_applied"] is True
