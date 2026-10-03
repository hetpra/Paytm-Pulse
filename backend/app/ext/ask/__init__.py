"""Grounded merchant questions using a small validated, non-SQL tool allowlist."""
from __future__ import annotations
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.repo import get_repo

FLAG="ask"; router=APIRouter()
class Question(BaseModel): question:str=Field(max_length=300)

def _sales(merchant_id):
    repo=get_repo(); skus=repo.list_skus(merchant_id); return skus,{s['id']:repo.get_sales(s['id'],30) for s in skus}
def answer(question:str, merchant_id="m1"):
    q=question.lower(); skus, sales=_sales(merchant_id)
    if re.search(r"run out|stock",q):
        from app.routes import risk_view
        items,_=risk_view(merchant_id); data=[{"name":x['name'],"status":x['_status'],"days_left":x['_forecast'].get('days_left')} for x in items if x['_status'] in ('critical','warning')]
        return {"tool":"stock_status","args":{},"data":data,"answer":"Items at risk: "+", ".join(f"{x['name']} ({x['days_left']:.1f} days)" for x in data)}
    if re.search(r"profit|margin",q):
        data=sorted([{"name":s['name'],"profit":sum(r['units_sold']*(s['sell_price']-s['unit_cost']) for r in sales[s['id']])} for s in skus],key=lambda x:x['profit'],reverse=True)
        return {"tool":"profit_by_item","args":{"days":30},"data":data[:5],"answer":f"Top profit item: {data[0]['name']} (₹{data[0]['profit']:,.0f})."}
    if re.search(r"weekday|saturday",q):
        data=[]
        for s in skus:
            total=sum(r['units_sold'] for r in sales[s['id']] if __import__('datetime').date.fromisoformat(r['sale_date']).weekday()==5); data.append({"name":s['name'],"saturday_units":total})
        data.sort(key=lambda x:x['saturday_units'],reverse=True); return {"tool":"sales_by_weekday","args":{"weekday":"Saturday"},"data":data[:5],"answer":f"Best seller on Saturday: {data[0]['name']} ({data[0]['saturday_units']} units)."}
    data=sorted([{"name":s['name'],"revenue":sum(r['units_sold']*s['sell_price'] for r in sales[s['id']])} for s in skus],key=lambda x:x['revenue'],reverse=True)
    return {"tool":"top_items","args":{"metric":"revenue","days":30,"n":5},"data":data[:5],"answer":f"Best seller: {data[0]['name']} at ₹{data[0]['revenue']:,.0f} in sales."}
@router.post("/")
def ask(body:Question,merchant_id:str="m1"): return answer(body.question,merchant_id)
def setup(app): pass
