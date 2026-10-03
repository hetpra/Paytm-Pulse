from tests.ext.conftest import client_for


SALES = "date,item_id,item_name,units_sold\n2026-09-01,a,Apple,3\n2026-09-02,a,Apple,4\n"
CATALOG = "item_id,item_name,unit_cost,sell_price,current_stock,lead_time_days,supplier_name\na,Apple,5,10,10,2,Fresh Co\n"


def test_byod_dry_run_and_apply():
    with client_for("byod") as client:
        response = client.post("/api/ext/byod/upload?dry_run=1", files={"sales":("sales.csv",SALES,"text/csv"),"catalog":("catalog.csv",CATALOG,"text/csv")}, data={"store_name":"My Store","cash_balance":"1000"})
        assert response.json()["ok"] and client.get("/api/dashboard?merchant_id=m_user").status_code == 404
        response = client.post("/api/ext/byod/upload", files={"sales":("sales.csv",SALES,"text/csv"),"catalog":("catalog.csv",CATALOG,"text/csv")}, data={"store_name":"My Store","cash_balance":"1000"})
        assert response.json()["ok"]
        assert client.get("/api/dashboard?merchant_id=m_user").status_code == 200


def test_byod_rejects_unknown_item():
    with client_for("byod") as client:
        response = client.post("/api/ext/byod/upload", files={"sales":("sales.csv",SALES.replace(",a,Apple,",",unknown,Apple,"),"text/csv"),"catalog":("catalog.csv",CATALOG,"text/csv")})
    assert response.json()["ok"] is False
