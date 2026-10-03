"""Discovery and loading for opt-in Paytm Pulse extensions."""
from __future__ import annotations

import importlib
import logging
import os
import pkgutil

from fastapi import FastAPI

from app.ext import hooks

logger = logging.getLogger(__name__)
_INTERNAL = {"common", "hooks", "store"}


def _requested() -> set[str] | None:
    raw = os.getenv("EXT_ENABLED", "all").strip()
    if raw.lower() == "all":
        return None
    if raw.lower() in {"", "none"}:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def load_extensions(app: FastAPI) -> list[str]:
    """Load enabled packages, recording failures instead of failing startup."""
    hooks.clear()
    requested = _requested()
    available: list[str] = []
    candidates = []
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("_") or module.name in _INTERNAL:
            continue
        candidates.append(module.name)

    for name in candidates:
        try:
            module = importlib.import_module(f"{__name__}.{name}")
            flag = getattr(module, "FLAG", name)
            if flag not in available:
                available.append(flag)
            requires = getattr(module, "REQUIRES", [])
            enabled = requested is None or flag in requested
            if name.startswith("glue_"):
                enabled = requested is None or all(req in (requested or set()) for req in requires)
            if not enabled:
                continue
            module.setup(app)
            app.include_router(module.router, prefix=f"/api/ext/{flag}")
            app.state.enabled_extensions.append(flag)
        except Exception:
            logger.exception("Extension '%s' was disabled after setup failed", name)

    app.state.available_extensions = sorted(available)
    app.state.enabled_extensions.sort()
    return app.state.enabled_extensions
