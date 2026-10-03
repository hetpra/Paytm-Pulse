"""LangGraph workflow — the orchestration heart of Paytm Pulse."""

from __future__ import annotations
import logging
import uuid
import threading
import time
from functools import wraps
from datetime import date, datetime, timedelta, UTC
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from app.repo import get_repo
from app import planner, llm
from app.ext import hooks

logger = logging.getLogger(__name__)
_proposal_locks: dict[str, threading.Lock] = {}
_proposal_locks_guard = threading.Lock()


def traced(name: str):
    """Emit timing metadata without letting observer extensions affect nodes."""
    def decorate(fn):
        @wraps(fn)
        def wrapped(state: PulseState):
            started = time.perf_counter()
            thread_id = state.get("thread_id", "")
            hooks.emit("graph.step", node=name, status="start", ms=0,
                       state_keys=list(state.keys()), thread_id=thread_id,
                       merchant_id=state.get("merchant_id"), proposal_id=state.get("proposal_id"))
            try:
                result = fn(state)
                hooks.emit("graph.step", node=name, status="done",
                           ms=round((time.perf_counter() - started) * 1000, 2),
                           state_keys=list((result or {}).keys()), thread_id=thread_id,
                           merchant_id=state.get("merchant_id"), proposal_id=(result or {}).get("proposal_id", state.get("proposal_id")), result=result or {})
                return result
            except Exception:
                hooks.emit("graph.step", node=name, status="error",
                           ms=round((time.perf_counter() - started) * 1000, 2),
                           state_keys=list(state.keys()), thread_id=thread_id,
                           merchant_id=state.get("merchant_id"), proposal_id=state.get("proposal_id"))
                raise
        return wrapped
    return decorate


class PulseState(TypedDict, total=False):
    merchant_id: str
    at_risk: list
    plan: dict
    cash: dict
    alert_text: str
    proposal_id: str
    decision: dict
    result: dict


# ── Nodes ───────────────────────────────────────────────────────

@traced("load_and_select")
def load_and_select(state: PulseState) -> dict:
    """Read SKUs + cached forecasts + merchant; compute status; keep at-risk SKUs."""
    repo = get_repo()
    merchant_id = state["merchant_id"]
    merchant = repo.get_merchant(merchant_id)
    from app.routes import risk_view
    risk_skus, forecasts = risk_view(merchant_id)
    at_risk = [sku for sku in risk_skus if sku["_status"] in ("critical", "warning")]
    skus = [{k: v for k, v in sku.items() if not k.startswith("_")} for sku in risk_skus]
    return {"at_risk": at_risk, "plan": {"merchant": merchant, "forecasts": forecasts, "skus": skus}}


@traced("draft_po")
def draft_po(state: PulseState) -> dict:
    """Build line items and POs by supplier."""
    repo = get_repo()
    suppliers_list = repo.list_suppliers()
    suppliers = {s["id"]: s for s in suppliers_list}

    forecasts = state["plan"]["forecasts"]
    plan_result = planner.build_plan(state["at_risk"], forecasts, suppliers, state["plan"]["merchant"])

    return {"plan": {**state["plan"], **plan_result}}


@traced("check_cash")
def check_cash(state: PulseState) -> dict:
    """Compute cash available, gap, and loan offer."""
    merchant = state["plan"]["merchant"]
    total = state["plan"]["total"]
    limit = hooks.apply("lending.limit", merchant["preapproved_limit"], merchant=merchant)
    cash_result = planner.cash_check(
        merchant["cash_balance"],
        total,
        limit,
    )
    cash_result["loan_offer"] = hooks.apply("lending.offer", cash_result["loan_offer"],
                                            gap=cash_result["cash_gap"], total=total,
                                            merchant=merchant)
    return {"cash": cash_result}


@traced("write_alert")
def write_alert(state: PulseState) -> dict:
    """Generate alert text via LLM (with template fallback)."""
    plan = state["plan"]
    cash = state["cash"]
    line_items = plan.get("line_items", [])

    # Find top item (most critical / lowest days_left)
    if line_items:
        top = min(line_items, key=lambda x: x.get("days_left", 999))
        top_item = {"name": top["name"], "days_left": top["days_left"]}
    else:
        top_item = {"name": "item", "days_left": 1}

    facts = {
        "top_item": top_item,
        "items_at_risk": len(line_items),
        "total": plan.get("total", 0),
        "cash_available": cash.get("cash_available", 0),
        "loan_offer": cash.get("loan_offer"),
        "line_items": line_items,
    }

    alert_text = hooks.apply("llm.alert_text", llm.generate_alert(facts), facts=facts)
    return {"alert_text": alert_text}


@traced("save_proposal")
def save_proposal(state: PulseState) -> dict:
    """Persist the pending proposal."""
    repo = get_repo()
    plan = state["plan"]
    cash = state["cash"]
    merchant = plan["merchant"]
    forecasts = plan["forecasts"]
    skus = plan["skus"]

    proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    # Build the full proposal payload
    payload = {
        "id": proposal_id,
        "merchant_id": merchant["id"],
        "status": "pending",
        "alert_text": state["alert_text"],
        "line_items": plan.get("line_items", []),
        "purchase_orders": plan.get("purchase_orders", []),
        "subtotal": plan.get("subtotal", 0),
        "platform_fee": plan.get("platform_fee", 0),
        "total": plan.get("total", 0),
        "cash_available": cash.get("cash_available", 0),
        "cash_gap": cash.get("cash_gap", 0),
        "loan_offer": cash.get("loan_offer"),
        "revenue_at_risk_7d": planner.revenue_at_risk(skus, forecasts),
        "created_at": datetime.now(UTC).isoformat(),
    }

    payload = hooks.apply("proposal.payload", payload)
    proposal = repo.create_proposal({
        "id": proposal_id,
        "merchant_id": merchant["id"],
        "thread_id": thread_id,
        "status": "pending",
        "alert_text": state["alert_text"],
        "payload": payload,
        "created_at": datetime.now(UTC).isoformat(),
    })

    hooks.emit("proposal.created", proposal=proposal)
    return {"proposal_id": proposal_id}


@traced("await_approval")
def await_approval(state: PulseState) -> dict:
    """Pause for human approval — no side effects in this node."""
    decision = interrupt({"proposal_id": state["proposal_id"]})
    return {"decision": decision}


@traced("execute")
def execute(state: PulseState) -> dict:
    """Execute or reject based on decision."""
    repo = get_repo()
    proposal = repo.get_proposal(state["proposal_id"])
    if not proposal:
        return {"result": {"error": "Proposal not found"}}

    payload = proposal.get("payload", {})
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)

    decision = state.get("decision", {})
    merchant_id = proposal["merchant_id"]

    if decision.get("approved"):
        return _execute_approval(repo, proposal, payload, merchant_id)
    else:
        repo.update_proposal(state["proposal_id"], status="rejected", decided_at=datetime.now(UTC).isoformat())
        proposal = repo.get_proposal(state["proposal_id"])
        hooks.emit("proposal.rejected", proposal=proposal)
        return {"result": {"status": "rejected", "proposal": proposal}}


def _execute_approval(repo, proposal, payload, merchant_id: str) -> dict:
    """Execute planner rule 6: create POs + loan, update cash, mark incoming."""
    today = date.today()
    merchant = repo.get_merchant(merchant_id)
    proposal_id = proposal["id"]

    # Create POs
    created_pos = []
    for po_summary in payload.get("purchase_orders", []):
        # Find line items for this supplier
        items = [li for li in payload.get("line_items", []) if li["supplier_id"] == po_summary["supplier_id"]]
        po = {
            "id": f"po_{uuid.uuid4().hex[:8]}",
            "proposal_id": proposal_id,
            "merchant_id": merchant_id,
            "supplier_id": po_summary["supplier_id"],
            "items": items,
            "subtotal": po_summary["subtotal"],
            "platform_fee": po_summary["platform_fee"],
            "total": po_summary["total"],
            "status": "sent",
            "created_at": datetime.now(UTC).isoformat(),
        }
        repo.create_po(po)
        created_pos.append(po)

    # Create loan if applicable
    loan_offer = payload.get("loan_offer")
    created_loan = None
    principal = 0
    if loan_offer and loan_offer.get("principal", 0) > 0:
        principal = loan_offer["principal"]
        loan = {
            "id": f"loan_{uuid.uuid4().hex[:8]}",
            "proposal_id": proposal_id,
            "merchant_id": merchant_id,
            "principal": principal,
            "interest_rate_pct": loan_offer["interest_rate_pct"],
            "interest": loan_offer["interest"],
            "processing_fee": loan_offer["processing_fee"],
            "tenure_days": loan_offer["tenure_days"],
            "total_repayment": loan_offer["total_repayment"],
            "status": "disbursed",
            "created_at": datetime.now(UTC).isoformat(),
        }
        repo.create_loan(loan)
        created_loan = loan

    # Update cash balance: cash_balance += principal − total
    total = payload.get("total", 0)
    new_cash = merchant["cash_balance"] + principal - total
    repo.update_merchant(merchant_id, cash_balance=new_cash)

    # Mark ordered SKUs as incoming
    for li in payload.get("line_items", []):
        sku_id = li["sku_id"]
        # Find the SKU to get lead time
        sku = next((s for s in repo.list_skus(merchant_id) if s["id"] == sku_id), None)
        if sku:
            eta = (today + timedelta(days=sku["lead_time_days"])).isoformat()
            repo.update_sku(sku_id, incoming_qty=li["qty"], incoming_eta=eta)

    # Mark proposal approved
    repo.update_proposal(proposal_id, status="approved", decided_at=datetime.now(UTC).isoformat())
    proposal = repo.get_proposal(proposal_id)
    hooks.emit("proposal.approved", proposal=proposal, purchase_orders=created_pos, loan=created_loan)
    return {
        "result": {
            "status": "approved",
            "proposal": proposal,
            "purchase_orders": created_pos,
            "loan": created_loan,
            "merchant": repo.get_merchant(merchant_id),
        }
    }


# ── Build the graph ─────────────────────────────────────────────

def _build_graph():
    g = StateGraph(PulseState)
    g.add_node("load_and_select", load_and_select)
    g.add_node("draft_po", draft_po)
    g.add_node("check_cash", check_cash)
    g.add_node("write_alert", write_alert)
    g.add_node("save_proposal", save_proposal)
    g.add_node("await_approval", await_approval)
    g.add_node("execute", execute)

    g.add_edge(START, "load_and_select")
    g.add_conditional_edges("load_and_select", lambda s: "draft_po" if s.get("at_risk") else END)
    g.add_edge("draft_po", "check_cash")
    g.add_edge("check_cash", "write_alert")
    g.add_edge("write_alert", "save_proposal")
    g.add_edge("save_proposal", "await_approval")
    g.add_edge("await_approval", "execute")
    g.add_edge("execute", END)

    return g.compile(checkpointer=MemorySaver())


# Process-wide graph instance
graph = _build_graph()


# ── Public API ──────────────────────────────────────────────────

def run_analyze(merchant_id: str) -> Optional[dict]:
    """
    Run the graph to the approval pause.
    Returns the proposal payload or None if nothing is at risk.
    Idempotent: returns existing pending proposal if there is one.
    """
    repo = get_repo()

    # Check for existing pending proposal
    existing = repo.get_pending_proposal(merchant_id)
    if existing:
        payload = existing.get("payload", {})
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        return payload

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    try:
        result = graph.invoke(
            {"merchant_id": merchant_id},
            {"configurable": {"thread_id": thread_id}},
        )
    except Exception as e:
        # interrupt raises GraphInterrupt — that's expected
        logger.debug(f"Graph paused at interrupt (expected): {e}")

    # Fetch the proposal that was just saved
    proposal = repo.get_pending_proposal(merchant_id)
    if proposal:
        # Update thread_id
        repo.update_proposal(proposal["id"], thread_id=thread_id)
        payload = proposal.get("payload", {})
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        return payload

    return None


def run_approve(proposal_id: str) -> dict:
    """Resume the graph with approval, or execute directly if thread is lost."""
    repo = get_repo()
    with _lock_for(proposal_id):
        proposal = repo.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.get("status") != "pending":
            raise RuntimeError(proposal)

        thread_id = proposal.get("thread_id")

    # Try to resume the graph
        if thread_id:
            try:
                result = graph.invoke(Command(resume={"approved": True}), {"configurable": {"thread_id": thread_id}})
                if isinstance(result, dict) and "result" in result:
                    return result["result"]
            except Exception as e:
                logger.warning(f"Graph resume failed ({e}), executing directly")

    # Fallback: execute directly from stored proposal payload
        payload = proposal.get("payload", {})
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        return _execute_approval(repo, proposal, payload, proposal["merchant_id"])["result"]


def run_reject(proposal_id: str) -> dict:
    """Reject a proposal."""
    repo = get_repo()
    with _lock_for(proposal_id):
        proposal = repo.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.get("status") != "pending":
            raise RuntimeError(proposal)

        thread_id = proposal.get("thread_id")

        if thread_id:
            try:
                graph.invoke(Command(resume={"approved": False}), {"configurable": {"thread_id": thread_id}})
            except Exception:
                pass
        repo.update_proposal(proposal_id, status="rejected", decided_at=datetime.now(UTC).isoformat())
        decided = repo.get_proposal(proposal_id)
        hooks.emit("proposal.rejected", proposal=decided)
        return {"proposal": decided}


def _lock_for(proposal_id: str) -> threading.Lock:
    with _proposal_locks_guard:
        return _proposal_locks.setdefault(proposal_id, threading.Lock())
