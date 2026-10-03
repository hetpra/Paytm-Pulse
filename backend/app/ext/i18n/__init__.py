"""Precomputed Hindi/Hinglish alert variants, with no LLM required."""
from __future__ import annotations

import math
from fastapi import APIRouter
from app.ext import hooks

FLAG = "i18n"
router = APIRouter()


def _variants(payload: dict) -> dict:
    lines = payload.get("line_items", []); top = min(lines, key=lambda item:item.get("days_left", 999)) if lines else {"name":"item", "days_left":1}
    values = {"top":top["name"], "d":math.ceil(top.get("days_left", 1)), "n":len(lines), "total":f"{payload.get('total',0):,.0f}", "avail":f"{payload.get('cash_available',0):,.0f}"}
    loan = payload.get("loan_offer") or {}; suffix_hinglish = f" Aapke paas ₹{values['avail']} hain, isliye ₹{loan.get('principal', 0):,.0f} ka pre-approved Paytm Business Loan gap cover karega." if loan.get("principal") else ""
    suffix_hi = f" आपके पास ₹{values['avail']} उपलब्ध हैं, इसलिए ₹{loan.get('principal', 0):,.0f} का pre-approved Paytm Business Loan gap cover करेगा।" if loan.get("principal") else ""
    return {"hinglish":f"⚠️ {values['top']} {values['d']} din mein khatam ho jayega. {values['n']} items restock karne hain — ₹{values['total']} ka order.{suffix_hinglish} Order ke liye approve karein.", "hi":f"⚠️ {values['top']} लगभग {values['d']} दिन में खत्म हो जाएगा। {values['n']} आइटम रीस्टॉक करने हैं — ₹{values['total']} का ऑर्डर।{suffix_hi} ऑर्डर देने के लिए अप्रूव करें।"}


def add_i18n(payload: dict, **_) -> dict:
    payload["alert_i18n"] = _variants(payload)
    return payload


def setup(app) -> None:
    hooks.register_filter("proposal.payload", add_i18n)
