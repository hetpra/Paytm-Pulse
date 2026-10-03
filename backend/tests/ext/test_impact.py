from tests.ext.conftest import client_for


def test_impact_is_deterministic_and_protects_revenue():
    with client_for("impact") as client:
        first = client.get("/api/ext/impact/").json()
        second = client.get("/api/ext/impact/").json()
    assert first["net_gain"] == second["net_gain"]
    assert first["with"]["lost_revenue"] <= first["without"]["lost_revenue"]
    assert first["net_gain"] == round(first["without"]["lost_profit"] - first["with"]["lost_profit"] - first["costs"]["platform_fees"] - first["costs"]["loan_costs"], 2)
