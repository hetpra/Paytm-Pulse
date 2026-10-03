"""LLM integration — alert generation with auto-fallback to template."""

from __future__ import annotations
import logging
import math
from typing import Optional

from app.config import LLM_PROVIDER, LLM_MODEL, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Paytm Pulse, a friendly business copilot for small Indian shopkeepers. "
    "Write ONE short alert (max 60 words) in simple English, no jargon, no markdown. "
    "Mention the most urgent product and how many days of stock are left, how many items "
    "need restocking and the total order value, and — only if loan_offer is present — that "
    "a pre-approved Paytm Business Loan of that exact amount can cover the gap. "
    'End with: "Approve to place the order." Use ₹. '
    "Use ONLY the numbers given in the JSON; never invent or recompute numbers."
)


def template_alert(facts: dict) -> str:
    """Deterministic template fallback — always works."""
    top = facts.get("top_item", {})
    name = top.get("name", "item")
    days = math.ceil(top.get("days_left", 1))
    n = facts.get("items_at_risk", 0)
    total = facts.get("total", 0)
    avail = facts.get("cash_available", 0)
    loan = facts.get("loan_offer")

    # Count unique suppliers
    suppliers = set()
    for item in facts.get("line_items", []):
        suppliers.add(item.get("supplier_id", ""))
    k = len(suppliers) if suppliers else 1

    msg = (
        f"⚠️ {name} will run out in ~{days} day(s). "
        f"{n} items need restocking — order ₹{total:,.0f} from {k} distributor(s). "
        f"You have ₹{avail:,.0f} available"
    )

    if loan and loan.get("principal", 0) > 0:
        msg += f"; a pre-approved Paytm Business Loan of ₹{loan['principal']:,.0f} covers the gap"

    msg += ". Approve to place the order."
    return msg


def _call_openrouter(user_msg: str) -> Optional[str]:
    """Call OpenRouter (OpenAI-compatible API)."""
    import openai
    model = LLM_MODEL or "google/gemini-3.8-flash"
    logger.info(f"🤖 Calling OpenRouter with model: {model}...")
    client = openai.OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1500,
        timeout=15,
    )
    content = resp.choices[0].message.content.strip()
    logger.info(f"✅ OpenRouter response received: {content}")
    return content


def _call_anthropic(user_msg: str) -> Optional[str]:
    """Call Anthropic directly."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model = LLM_MODEL or "claude-haiku-4-5-20251001"
    resp = client.messages.create(
        model=model,
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text.strip()


def _call_openai(user_msg: str) -> Optional[str]:
    """Call OpenAI directly."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    model = LLM_MODEL or "gpt-4o-mini"
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=150,
        timeout=8,
    )
    return resp.choices[0].message.content.strip()


def generate_alert(facts: dict, language: str = "en") -> str:
    """
    Generate an alert message. 8s timeout; any failure → template_alert.

    facts: {top_item:{name,days_left}, items_at_risk, total, cash_available, loan_offer, line_items}
    """
    if LLM_PROVIDER == "none":
        return template_alert(facts)

    import json
    # Build user message (only the fields the LLM needs)
    user_payload = {
        "top_item": facts.get("top_item"),
        "items_at_risk": facts.get("items_at_risk"),
        "total": facts.get("total"),
        "cash_available": facts.get("cash_available"),
        "loan_offer": facts.get("loan_offer"),
    }
    if language != "en":
        user_payload["language"] = language

    user_msg = json.dumps(user_payload, ensure_ascii=False)

    try:
        if LLM_PROVIDER == "openrouter":
            result = _call_openrouter(user_msg)
        elif LLM_PROVIDER == "anthropic":
            result = _call_anthropic(user_msg)
        elif LLM_PROVIDER == "openai":
            result = _call_openai(user_msg)
        else:
            return template_alert(facts)

        if result:
            return result
    except Exception as e:
        logger.warning(f"LLM call failed ({e}), using template fallback")

    return template_alert(facts)
