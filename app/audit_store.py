"""In-memory ring of recent audit records for the admin console.

Stdout / Log Analytics remain the durable trail. This store is a short window
the Vercel UI can query without Azure credentials. Lost on process restart.
"""

from __future__ import annotations

from collections import deque
from threading import Lock

_MAX_RECORDS = 200


class AuditStore:
    def __init__(self, maxlen: int = _MAX_RECORDS) -> None:
        self._records: deque[dict] = deque(maxlen=maxlen)
        self._lock = Lock()

    def add(self, record: dict) -> None:
        with self._lock:
            self._records.appendleft(dict(record))

    def list(
        self,
        *,
        caller: str | None = None,
        agent_id: str | None = None,
        rule: str | None = None,
        decision: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        limit = max(1, min(limit, _MAX_RECORDS))
        with self._lock:
            items = list(self._records)
        out: list[dict] = []
        for item in items:
            if caller and item.get("caller") != caller:
                continue
            if agent_id and item.get("agent_id") != agent_id:
                continue
            if rule and item.get("rule") != rule:
                continue
            if decision and not str(item.get("decision", "")).startswith(decision):
                continue
            out.append(item)
            if len(out) >= limit:
                break
        return out

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


audit_store = AuditStore()
