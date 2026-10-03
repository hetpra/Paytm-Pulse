"""Supplier price choice and an idempotent distributor PO progression portal."""
from __future__ import annotations
import math
from datetime import date, datetime, UTC
from fastapi import APIRouter, HTTPException
from app.ext import hooks
from app.ext.store import get_table
from app.repo import get_repo

FLAG="distributor"; router=APIRouter(); STEPS=["sent","accepted","dispatched","delivered"]
MULTIPLIERS=[.97,1.03,.98,1.02,.96,1.04,.99,1.01]

def seed_prices(**_):
    table=get_table("supplier_prices"); table.clear(); repo=get_repo(); suppliers=repo.list_suppliers()
    if len(suppliers)<2:return
    for index,sku in enumerate(repo.list_skus("m1")):
        default=next((s for s in suppliers if s['id']==sku['supplier_id']),suppliers[0]); other=next(s for s in suppliers if s['id']!=default['id'])
        table.insert({"id":f"{sku['id']}_{default['id']}","sku_id":sku['id'],"supplier_id":default['id'],"supplier_name":default['name'],"unit_cost":sku['unit_cost'],"lead_days":sku['lead_time_days']})
        table.insert({"id":f"{sku['id']}_{other['id']}","sku_id":sku['id'],"supplier_id":other['id'],"supplier_name":other['name'],"unit_cost":round(sku['unit_cost']*MULTIPLIERS[index],2),"lead_days":max(1,sku['lead_time_days']-1) if index%2==0 else sku['lead_time_days']+1})

def choose(items:list[dict],**_):
    prices=get_table("supplier_prices")
    for item in items:
        options=prices.list(sku_id=item['sku_id'])
        if not options:continue
        qualified=[row for row in options if row['lead_days']<=max(1,math.floor(item.get('days_left',1)))]
        choice=min(qualified or options,key=lambda row:(row['unit_cost'],row['lead_days']) if qualified else (row['lead_days'],row['unit_cost']))
        alternatives=[row for row in options if row['id']!=choice['id']]
        item.update({"supplier_id":choice['supplier_id'],"supplier_name":choice['supplier_name'],"unit_cost":choice['unit_cost'],"line_total":round(choice['unit_cost']*item['qty'],2),"savings_vs_default":round((item['unit_cost']-choice['unit_cost'])*item['qty'],2)})
        if alternatives:item['alt_supplier']={k:alternatives[0][k] for k in ('supplier_name','unit_cost','lead_days')}
    return items

def on_approved(*,purchase_orders:list[dict],**_):
    table=get_table("po_tracking")
    for po in purchase_orders:
        if not table.get(po['id']):table.insert({"id":po['id'],"po_id":po['id'],"status":"sent","delivered_applied":False})

@router.get("/pos")
def pos(supplier_id:str|None=None,merchant_id:str="m1"):
    rows=get_repo().list_pos(merchant_id); out=[]
    for po in rows:
        if supplier_id and po['supplier_id']!=supplier_id:continue
        out.append({**po,"tracking":get_table("po_tracking").get(po['id']) or {"status":"sent"}})
    return {"purchase_orders":out}

@router.post("/pos/{po_id}/advance")
def advance(po_id:str,merchant_id:str="m1"):
    table=get_table("po_tracking"); tracking=table.get(po_id)
    if not tracking: raise HTTPException(404,"PO tracking not found")
    index=STEPS.index(tracking['status'])
    if index==len(STEPS)-1:return {"tracking":tracking}
    status=STEPS[index+1]; tracking=table.update(po_id,status=status)
    if status=="delivered" and not tracking.get("delivered_applied"):
        po=next((row for row in get_repo().list_pos(merchant_id) if row['id']==po_id),None)
        if po:
            for item in po['items']:
                sku=next((s for s in get_repo().list_skus(merchant_id) if s['id']==item['sku_id']),None)
                if sku:get_repo().update_sku(sku['id'],current_stock=sku['current_stock']+item['qty'],incoming_qty=0,incoming_eta=None)
        tracking=table.update(po_id,delivered_applied=True)
    return {"tracking":tracking}

def setup(app):
    hooks.register_event("data.seeded",seed_prices)
    hooks.register_filter("planner.line_items",choose)
    hooks.register_event("proposal.approved",on_approved)
