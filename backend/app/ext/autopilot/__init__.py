"""Premium-only, rule-bound simulated scheduled approval."""
from __future__ import annotations
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ext.store import get_table
from app.repo import get_repo

FLAG="autopilot"; router=APIRouter()
DEFAULT={"enabled":False,"max_order_value":30000,"max_loan_amount":25000,"critical_only":True}
class Settings(BaseModel): enabled:bool=False; max_order_value:float=30000; max_loan_amount:float=25000; critical_only:bool=True
def _settings(merchant_id): return get_table("autopilot_settings").get(merchant_id) or {"id":merchant_id,**DEFAULT}
def _notification(merchant_id,message): return get_table("notifications").insert({"merchant_id":merchant_id,"message":message,"read":False,"created_at":datetime.now(UTC).isoformat()})
def allowed(proposal,merchant,settings):
    loan=proposal.get("loan_offer"); critical=any(item.get("status")=="critical" for item in proposal.get("line_items",[]))
    return merchant.get("plan")=="premium" and settings["enabled"] and proposal["total"]<=settings["max_order_value"] and (not loan or (settings["max_loan_amount"]>0 and loan["principal"]<=settings["max_loan_amount"])) and (not settings["critical_only"] or critical)
def run_once(merchant_id="m1"):
    from app.graph import run_analyze,run_approve
    proposal=run_analyze(merchant_id); _notification(merchant_id,"Pulse analyzed today’s inventory")
    merchant=get_repo().get_merchant(merchant_id); settings=_settings(merchant_id)
    if proposal and allowed(proposal,merchant,settings):
        result=run_approve(proposal["id"]); _notification(merchant_id,"Auto-approved by your rule")
        return {"proposal":proposal,"auto_approved":True,"result":result}
    return {"proposal":proposal,"auto_approved":False}
@router.post("/run")
def run(merchant_id:str="m1"): return run_once(merchant_id)
@router.get("/settings")
def settings(merchant_id:str="m1"): return _settings(merchant_id)
@router.put("/settings")
def update(body:Settings,merchant_id:str="m1"):
    table=get_table("autopilot_settings"); fields=body.model_dump()
    return table.update(merchant_id,**fields) or table.insert({"id":merchant_id,**fields})
@router.get("/notifications")
def notifications(merchant_id:str="m1"): return {"notifications":sorted(get_table("notifications").list(merchant_id=merchant_id),key=lambda x:x["created_at"],reverse=True)}
@router.post("/notifications/{notification_id}/read")
def read(notification_id:str):
    row=get_table("notifications").update(notification_id,read=True)
    if not row: raise HTTPException(404,"Notification not found")
    return row
def setup(app): pass
