"""Bring-your-own catalog and item sales data, isolated from demo merchant data."""
from __future__ import annotations
import csv, io
from datetime import date
from fastapi import APIRouter, UploadFile, File, Form, Query
from app.ext import hooks
from app.ext.store import get_table
from app.repo import get_repo

FLAG="byod"; router=APIRouter()
SALES_COLS={"date","item_id","item_name","units_sold"}; CATALOG_COLS={"item_id","item_name","unit_cost","sell_price","current_stock","lead_time_days","supplier_name"}

def _rows(upload: UploadFile) -> list[dict]:
    return list(csv.DictReader(io.StringIO(upload.file.read().decode("utf-8-sig"))))

def validate(sales: list[dict], catalog: list[dict]) -> tuple[list[str],list[str]]:
    errors=[]; warnings=[]
    if not sales or not SALES_COLS <= set(sales[0]): errors.append("sales.csv is missing required columns")
    if not catalog or not CATALOG_COLS <= set(catalog[0]): errors.append("catalog.csv is missing required columns")
    if errors: return errors,warnings
    items={row["item_id"] for row in catalog}
    dates: dict[str,set[str]]={}
    for row in sales:
        try: date.fromisoformat(row["date"]); units=int(row["units_sold"]); assert units >= 0
        except Exception: errors.append(f"Invalid sales row for {row.get('item_id','item')}"); continue
        if row["item_id"] not in items: errors.append(f"Sales item {row['item_id']} is not in catalog")
        dates.setdefault(row["item_id"],set()).add(row["date"])
    for row in catalog:
        try:
            assert float(row["unit_cost"]) >= 0 and float(row["sell_price"]) >= 0 and int(row["current_stock"]) >= 0 and int(row["lead_time_days"]) >= 0
        except Exception: errors.append(f"Invalid catalog row for {row.get('item_id','item')}")
    if len(catalog)>50 or len(sales)>50000: errors.append("Maximum is 50 SKUs and 50,000 sales rows")
    for item, days in dates.items():
        if len(days)<28: warnings.append(f"{item} has fewer than 28 sales days; fallback forecast may be used")
    return errors,warnings

@router.get("/template/{kind}")
def template(kind:str):
    header = ",".join(sorted(SALES_COLS if kind=="sales" else CATALOG_COLS))
    return __import__('fastapi').responses.PlainTextResponse(header+"\n", media_type="text/csv")

@router.post("/upload")
async def upload(sales:UploadFile=File(...), catalog:UploadFile=File(...), store_name:str=Form("My Store"), cash_balance:float=Form(0), dry_run:int=Query(0)):
    sales_rows,catalog_rows=_rows(sales),_rows(catalog); errors,warnings=validate(sales_rows,catalog_rows)
    result={"ok":not errors,"errors":errors,"warnings":warnings,"skus":len(catalog_rows),"rows":len(sales_rows),"date_range":([min(r['date'] for r in sales_rows),max(r['date'] for r in sales_rows)] if sales_rows else None)}
    if errors or dry_run: return result
    repo=get_repo(); repo.delete_merchant_data("m_user") if repo.get_merchant("m_user") else None
    supplier_names=sorted({row['supplier_name'] for row in catalog_rows}); suppliers=[{"id":f"user_sup_{i}","name":name,"city":None} for i,name in enumerate(supplier_names)]
    supplier_id={row['name']:row['id'] for row in suppliers}
    skus=[{"id":f"user_{row['item_id']}","merchant_id":"m_user","supplier_id":supplier_id[row['supplier_name']],"name":row['item_name'],"emoji":row.get('emoji','📦'),"unit_cost":float(row['unit_cost']),"sell_price":float(row['sell_price']),"current_stock":int(row['current_stock']),"incoming_qty":0,"incoming_eta":None,"lead_time_days":int(row['lead_time_days'])} for row in catalog_rows]
    repo.seed_base({"id":"m_user","name":store_name,"owner_name":"Store owner","cash_balance":cash_balance,"preapproved_limit":0,"plan":"free"}, suppliers, skus)
    lookup={row['item_id']:f"user_{row['item_id']}" for row in catalog_rows}; repo.bulk_insert_sales([{"sku_id":lookup[row['item_id']],"sale_date":row['date'],"units_sold":int(row['units_sold'])} for row in sales_rows])
    from app.forecast import run_all_forecasts
    run_all_forecasts("m_user"); get_table("byod_meta").insert({"id":"m_user","store_name":store_name,"status":"ready","rows":len(sales_rows)})
    hooks.emit("data.changed", merchant_id="m_user"); return result

@router.get("/status")
def status(): return get_table("byod_meta").get("m_user") or {"status":"not_uploaded"}

@router.delete("/")
def remove():
    repo=get_repo()
    if repo.get_merchant("m_user"): repo.delete_merchant_data("m_user")
    get_table("byod_meta").delete("m_user"); return {"ok":True}

def cleanup(**payload):
    if payload.get("kind")=="reset":
        repo=get_repo()
        if repo.get_merchant("m_user"): repo.delete_merchant_data("m_user")
        get_table("byod_meta").delete("m_user")
def setup(app): hooks.register_event("data.seeded",cleanup)
