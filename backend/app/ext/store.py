"""Small namespace store for extensions.

The memory implementation is deliberately isolated from core repository
tables. A production Supabase deployment can replace this adapter with the
provided ``ext_kv`` migration without changing extension code.
"""
from __future__ import annotations

import copy
import uuid
from collections import defaultdict
from typing import Any

_tables: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)


class Table:
    def __init__(self, namespace: str):
        self.namespace = namespace

    @property
    def _rows(self) -> dict[str, dict[str, Any]]:
        return _tables[self.namespace]

    def insert(self, row: dict[str, Any]) -> dict[str, Any]:
        saved = copy.deepcopy(row)
        saved.setdefault("id", uuid.uuid4().hex)
        self._rows[saved["id"]] = saved
        return copy.deepcopy(saved)

    def get(self, id: str) -> dict[str, Any] | None:
        row = self._rows.get(id)
        return copy.deepcopy(row) if row else None

    def list(self, **eq_filters: Any) -> list[dict[str, Any]]:
        return [copy.deepcopy(row) for row in self._rows.values()
                if all(row.get(key) == value for key, value in eq_filters.items())]

    def update(self, id: str, **fields: Any) -> dict[str, Any] | None:
        if id not in self._rows:
            return None
        self._rows[id].update(copy.deepcopy(fields))
        return copy.deepcopy(self._rows[id])

    def delete(self, id: str) -> bool:
        return self._rows.pop(id, None) is not None

    def clear(self) -> None:
        self._rows.clear()


def get_table(namespace: str) -> Table:
    return Table(namespace)
