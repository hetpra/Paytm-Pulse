from app.ext.lending import floor_500
from tests.ext.conftest import client_for


def test_lending_adds_explainable_offer():
    with client_for("lending") as client:
        proposal = client.post("/api/analyze", json={"merchant_id":"m1"}).json()["proposal"]
    assert proposal["loan_offer"] is not None
    assert proposal["loan_offer"]["apr_pct"] > 0
    assert proposal["loan_offer"]["eligibility"]["limit"] >= 5000


def test_floor_500():
    assert floor_500(17307.7) == 17000
