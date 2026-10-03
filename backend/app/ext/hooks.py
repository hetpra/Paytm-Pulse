"""Fault-isolated extension hooks.

Extensions may enrich values or observe events, but must never interrupt the
core merchant flow.  Keeping this module dependency-free also makes hooks safe
to import from planner and forecasting code.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)
_filters: dict[str, list[tuple[int, Callable[..., Any]]]] = defaultdict(list)
_events: dict[str, list[Callable[..., Any]]] = defaultdict(list)


def register_filter(name: str, fn: Callable[..., Any], priority: int = 50) -> None:
    _filters[name].append((priority, fn))
    _filters[name].sort(key=lambda item: item[0])


def register_event(name: str, fn: Callable[..., Any]) -> None:
    _events[name].append(fn)


def apply(name: str, value: Any, **ctx: Any) -> Any:
    for _, fn in _filters.get(name, []):
        try:
            value = fn(value, **ctx)
        except Exception:
            logger.exception("Extension filter '%s' failed; preserving prior value", name)
    return value


def emit(name: str, **payload: Any) -> None:
    for fn in _events.get(name, []):
        try:
            fn(**payload)
        except Exception:
            logger.exception("Extension event '%s' failed", name)


def clear() -> None:
    """Test helper: remove registered callbacks between app factories."""
    _filters.clear()
    _events.clear()
