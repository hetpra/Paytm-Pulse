"""Repo package — factory function picks implementation by DB_MODE."""

from __future__ import annotations
import logging
from typing import Optional

from app.repo.base import BaseRepo
from app.repo.memory_repo import MemoryRepo

logger = logging.getLogger(__name__)

_repo: Optional[BaseRepo] = None


def get_repo() -> BaseRepo:
    """Return the singleton repo instance. Picks by DB_MODE; falls back to memory on error."""
    global _repo
    if _repo is not None:
        return _repo

    from app.config import DB_MODE, SUPABASE_URL, SUPABASE_SERVICE_KEY

    if DB_MODE == "supabase" and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            from app.repo.supabase_repo import SupabaseRepo
            _repo = SupabaseRepo(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.info("Using Supabase repo")
            return _repo
        except Exception as e:
            logger.warning(f"Supabase init failed ({e}), falling back to memory repo")

    _repo = MemoryRepo()
    logger.info("Using in-memory repo")
    return _repo


def reset_repo() -> None:
    """Reset the singleton (used in tests)."""
    global _repo
    _repo = None
