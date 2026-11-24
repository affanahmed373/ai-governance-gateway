"""Signed human-approval tokens and an in-memory pending queue.

High-impact tools used to trust a caller-declared `human_approved` boolean.
The admin console mints an HMAC token instead; `check_agent_action` verifies it.
See docs/adr/0010-signed-approval-tokens.md.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from threading import Lock

# Demo default so local and portfolio runs work without extra setup.
# Override in every real deploy.
_DEFAULT_SECRET = "dev-only-change-me"
_DEFAULT_TTL_SECONDS = 15 * 60
_MAX_PENDING = 100


def _env(*names: str, default: str) -> str:
    """Prefer Azure-safe names (lowercase + hyphens), then classic UPPER_SNAKE."""
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def approval_secret() -> str:
    return _env("gateway-approval-secret", "GATEWAY_APPROVAL_SECRET", default=_DEFAULT_SECRET)


def admin_token() -> str:
    return _env("gateway-admin-token", "GATEWAY_ADMIN_TOKEN", default="dev-admin-token")


def token_ttl_seconds() -> int:
    raw = _env(
        "gateway-approval-ttl-seconds",
        "GATEWAY_APPROVAL_TTL_SECONDS",
        default=str(_DEFAULT_TTL_SECONDS),
    )
    try:
        return max(60, int(raw))
    except ValueError:
        return _DEFAULT_TTL_SECONDS


def _sign(payload_b64: str) -> str:
    return hmac.new(
        approval_secret().encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()


def issue_approval_token(
    *,
    agent_id: str,
    tool: str,
    purpose: str,
    caller: str,
    ttl_seconds: int | None = None,
) -> dict:
    """Return {token, expires_at} bound to this agent/tool/purpose/caller."""
    ttl = ttl_seconds if ttl_seconds is not None else token_ttl_seconds()
    expires_at = int(time.time()) + ttl
    body = {
        "agent_id": agent_id,
        "tool": tool,
        "purpose": purpose,
        "caller": caller,
        "exp": expires_at,
    }
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    token = f"{payload_b64}.{_sign(payload_b64)}"
    return {"token": token, "expires_at": expires_at}


def verify_approval_token(
    token: str | None,
    *,
    agent_id: str,
    tool: str,
    purpose: str,
    caller: str,
) -> bool:
    if not token or "." not in token:
        return False
    payload_b64, signature = token.rsplit(".", 1)
    expected = _sign(payload_b64)
    if not hmac.compare_digest(signature, expected):
        return False
    pad = "=" * (-len(payload_b64) % 4)
    try:
        body = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
    except (json.JSONDecodeError, ValueError):
        return False
    if int(body.get("exp", 0)) < int(time.time()):
        return False
    return (
        body.get("agent_id") == agent_id
        and body.get("tool") == tool
        and body.get("purpose") == purpose
        and body.get("caller") == caller
    )


class PendingApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}
        self._lock = Lock()

    def enqueue(self, action: dict) -> dict:
        """Store a denied high-impact action for a reviewer. Drops oldest over cap."""
        item = {
            "id": str(uuid.uuid4()),
            "status": "pending",
            "created_at": int(time.time()),
            "action": action,
        }
        with self._lock:
            while len(self._items) >= _MAX_PENDING:
                oldest = min(self._items.values(), key=lambda x: x["created_at"])
                self._items.pop(oldest["id"], None)
            self._items[item["id"]] = item
        return item

    def list_pending(self) -> list[dict]:
        with self._lock:
            pending = [i for i in self._items.values() if i["status"] == "pending"]
        return sorted(pending, key=lambda x: x["created_at"], reverse=True)

    def get(self, approval_id: str) -> dict | None:
        with self._lock:
            item = self._items.get(approval_id)
            return dict(item) if item else None

    def approve(self, approval_id: str, reviewer: str) -> dict | None:
        with self._lock:
            item = self._items.get(approval_id)
            if item is None or item["status"] != "pending":
                return None
            action = item["action"]
            issued = issue_approval_token(
                agent_id=action["agent_id"],
                tool=action["tool"],
                purpose=action["purpose"],
                caller=action["caller"],
            )
            item["status"] = "approved"
            item["reviewer"] = reviewer
            item["approved_at"] = int(time.time())
            item["approval_token"] = issued["token"]
            item["expires_at"] = issued["expires_at"]
            return dict(item)

    def reject(self, approval_id: str, reviewer: str) -> dict | None:
        with self._lock:
            item = self._items.get(approval_id)
            if item is None or item["status"] != "pending":
                return None
            item["status"] = "rejected"
            item["reviewer"] = reviewer
            item["rejected_at"] = int(time.time())
            return dict(item)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


pending_approvals = PendingApprovalStore()
