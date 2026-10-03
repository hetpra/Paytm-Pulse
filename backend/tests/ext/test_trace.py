from tests.ext.conftest import client_for


def test_trace_records_workflow():
    with client_for("trace") as client:
        proposal = client.post("/api/analyze", json={"merchant_id":"m1"}).json()["proposal"]
        events = client.get("/api/ext/trace/").json()["events"]
        client.post(f"/api/proposals/{proposal['id']}/approve")
        after = client.get("/api/ext/trace/").json()["events"]
    assert any(event["node"] == "save_proposal" for event in events)
    assert any(event["node"] == "decision" for event in after)
