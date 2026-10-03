from tests.ext.conftest import client_for


def test_insights_seed_has_cards():
    with client_for("insights") as client:
        payload = client.get("/api/ext/insights/").json()
    assert len(payload["insights"]) >= 4
    assert payload["summary_text"]
