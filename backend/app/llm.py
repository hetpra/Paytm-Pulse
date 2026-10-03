"""Provider-neutral, failure-safe LLM helpers."""
from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
SYSTEM_PROMPT = "You are Paytm Pulse. Write one short friendly stock alert using only supplied facts."


class TransportError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _settings() -> tuple[str, str, str, str, float]:
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
    base = os.getenv("LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip()
    key = os.getenv("LLM_API_KEY", "").strip()
    timeout = float(os.getenv("LLM_TIMEOUT_S", "8"))
    if provider == "openrouter":
        provider, base, key = "openai_compat", base or "https://openrouter.ai/api/v1", key or os.getenv("OPENROUTER_API_KEY", "")
    elif provider == "openai":
        provider, base, key = "openai_compat", base or "https://api.openai.com/v1", key or os.getenv("OPENAI_API_KEY", "")
    elif provider == "anthropic":
        key = key or os.getenv("ANTHROPIC_API_KEY", "")
    return provider, base, model, key, timeout


def llm_mode() -> str:
    provider, _, model, _, _ = _settings()
    return "none" if provider == "none" else f"{provider}:{model or 'unconfigured'}"


def extract_json(text: str) -> Any | None:
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith(fence):
            text = text.rstrip()[:-3]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(url, data=json.dumps(payload).encode(), headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except HTTPError as error:
        raise TransportError(f"HTTP {error.code}", error.code) from error
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise TransportError(str(error)) from error


def _complete_compat(system: str, user: str, json_mode: bool, max_tokens: int, temperature: float) -> str | None:
    _, base, model, key, timeout = _settings()
    if not base or not model or not key:
        logger.warning("openai_compat requires LLM_BASE_URL, LLM_MODEL and LLM_API_KEY")
        return None
    payload: dict[str, Any] = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": max_tokens, "temperature": temperature}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    data = _post_json(f"{base}/chat/completions", {"Authorization": f"Bearer {key}"}, payload, timeout)
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def _complete_anthropic(system: str, user: str, json_mode: bool, max_tokens: int, temperature: float) -> str | None:
    _, base, model, key, timeout = _settings()
    if not model or not key:
        logger.warning("anthropic requires LLM_MODEL and LLM_API_KEY")
        return None
    if json_mode:
        user += "\nReturn a JSON object only."
    data = _post_json(f"{base or 'https://api.anthropic.com/v1'}/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"}, {"model": model, "max_tokens": max_tokens, "temperature": temperature, "system": system, "messages": [{"role": "user", "content": user}]}, timeout)
    try:
        return data["content"][0]["text"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def complete(system: str, user: str, *, json_mode: bool = False, max_tokens: int = 300, temperature: float = 0.2) -> str | None:
    provider, _, model, _, _ = _settings()
    if provider == "none":
        return None
    caller = {"openai_compat": _complete_compat, "anthropic": _complete_anthropic}.get(provider)
    if caller is None:
        logger.warning("Unknown LLM provider: %s", provider)
        return None
    started = time.perf_counter()
    for attempt in range(2):
        try:
            output = caller(system, user, json_mode, max_tokens, temperature)
            if output is not None and (not json_mode or extract_json(output) is not None):
                logger.info("LLM provider=%s model=%s latency_ms=%.1f", provider, model, (time.perf_counter() - started) * 1000)
                return output
            return None
        except TransportError as error:
            if attempt == 0 and error.status in {429, 500, 502, 503, 504}:
                time.sleep(0.5)
                continue
            logger.warning("LLM failure provider=%s model=%s error=%s", provider, model, error)
            return None
        except Exception as error:
            logger.warning("LLM failure provider=%s model=%s error=%s", provider, model, error)
            return None
    return None


def template_alert(facts: dict) -> str:
    top = facts.get("top_item", {})
    name, days = top.get("name", "item"), math.ceil(top.get("days_left", 1))
    count, total, cash = facts.get("items_at_risk", 0), facts.get("total", 0), facts.get("cash_available", 0)
    suppliers = {item.get("supplier_id", "") for item in facts.get("line_items", [])}
    message = f"Alert: {name} will run out in {days} day(s). {count} items need restocking. Order Rs {total:,.0f} from {len(suppliers) or 1} distributor(s). You have Rs {cash:,.0f} available"
    loan = facts.get("loan_offer")
    if loan and loan.get("principal", 0) > 0:
        message += f"; a pre-approved Paytm Business Loan of Rs {loan['principal']:,.0f} covers the gap"
    return message + ". Approve to place the order."


def generate_alert(facts: dict, language: str = "en") -> str:
    payload = {"top_item": facts.get("top_item"), "items_at_risk": facts.get("items_at_risk"), "total": facts.get("total"), "cash_available": facts.get("cash_available"), "loan_offer": facts.get("loan_offer"), "language": language}
    return complete(SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False), max_tokens=150) or template_alert(facts)


if __name__ == "__main__":
    import sys
    print(complete("Reply concisely.", " ".join(sys.argv[1:]) or "say ok") or "[template fallback]")
