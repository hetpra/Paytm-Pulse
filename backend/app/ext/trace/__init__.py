"""A transparent, fault-isolated execution trace for the approval workflow."""
from __future__ import annotations

from datetime import datetime, UTC
from fastapi import APIRouter
from app.ext import hooks
from app.ext.store import get_table

FLAG = "trace"
router = APIRouter()


def summary(node: str, result: dict | None = None) -> str:
    messages = {"load_and_select":"Loaded inventory risk", "draft_po":"Drafted supplier purchase orders", "check_cash":"Checked cash and loan eligibility", "write_alert":"Prepared merchant alert", "save_proposal":"Saved approval proposal", "await_approval":"Waiting for merchant approval", "execute":"Orders placed and funding processed"}
    return messages.get(node, node.replace("_", " ").title())


def record_step(**payload) -> None:
    if payload.get("status") != "done": return
    get_table("trace_events").insert({"thread_id":payload.get("thread_id", ""), "proposal_id":payload.get("proposal_id"), "merchant_id":payload.get("merchant_id"), "node":payload.get("node"), "status":"done", "ms":payload.get("ms", 0), "ts":datetime.now(UTC).isoformat(), "summary":summary(payload.get("node", ""), payload.get("result"))})


def decision_event(*, proposal: dict, **_) -> None:
    get_table("trace_events").insert({"thread_id":proposal.get("thread_id", ""), "proposal_id":proposal["id"], "merchant_id":proposal["merchant_id"], "node":"decision", "status":"done", "ms":0, "ts":datetime.now(UTC).isoformat(), "summary":"Orders placed · loan disbursed" if proposal.get("status") == "approved" else "Proposal dismissed"})


@router.get("/")
def events(proposal_id: str | None = None, merchant_id: str = "m1"):
    rows = get_table("trace_events").list(merchant_id=merchant_id)
    if proposal_id: rows = [row for row in rows if row.get("proposal_id") == proposal_id]
    return {"events": sorted(rows, key=lambda row: row["ts"])}


def setup(app) -> None:
    hooks.register_event("graph.step", record_step)
    hooks.register_event("proposal.approved", decision_event)
    hooks.register_event("proposal.rejected", decision_event)
