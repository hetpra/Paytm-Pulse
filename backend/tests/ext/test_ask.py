from tests.ext.conftest import client_for


def test_ask_uses_allowlisted_fallback_tools():
    with client_for("ask") as client:
        response = client.post("/api/ext/ask/", json={"question":"What will run out this week?"})
    assert response.status_code == 200
    assert response.json()["tool"] == "stock_status"


def test_ask_rejects_long_question():
    with client_for("ask") as client:
        response = client.post("/api/ext/ask/", json={"question":"x" * 301})
    assert response.status_code == 422
