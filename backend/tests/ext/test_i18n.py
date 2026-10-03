from app.ext.i18n import _variants
from tests.ext.conftest import client_for


def test_templates_keep_business_numbers():
    variants = _variants({"line_items":[{"name":"Parle-G","days_left":1.7}], "total":24221, "cash_available":5000, "loan_offer":{"principal":19500}})
    assert "24,221" in variants["hi"] and "19,500" in variants["hinglish"]


def test_proposal_contains_translations():
    with client_for("i18n") as client:
        proposal = client.post("/api/analyze", json={"merchant_id":"m1"}).json()["proposal"]
    assert {"hi", "hinglish"} <= proposal["alert_i18n"].keys()
