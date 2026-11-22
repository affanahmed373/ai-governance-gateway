from fastapi.testclient import TestClient

from app.approval import admin_token, pending_approvals
from app.audit_store import audit_store
from app.main import app

client = TestClient(app)
ADMIN = {"X-Admin-Token": admin_token()}


def setup_function() -> None:
    pending_approvals.clear()
    audit_store.clear()


def _delete_invoice_body(**overrides):
    body = {
        "agent_id": "spice-invoice-agent",
        "tool": "delete_invoice",
        "model": "gpt-4o-mini-eu",
        "prompt": "delete invoice 42",
        "purpose": "supplier_price_check",
        "lawful_basis": "contract",
        "environment": "prod",
        "data_class": "internal",
        "caller": "team-a",
    }
    body.update(overrides)
    return body


def test_high_impact_deny_enqueues_and_token_allows_retry():
    denied = client.post("/v1/agent/act", json=_delete_invoice_body())
    assert denied.status_code == 403
    detail = denied.json()["detail"]
    assert detail["detail"] == "human_approval_required"
    pending_id = detail["pending_approval_id"]

    listed = client.get("/v1/admin/approvals", headers=ADMIN)
    assert listed.status_code == 200
    assert any(item["id"] == pending_id for item in listed.json()["items"])

    approved = client.post(
        f"/v1/admin/approvals/{pending_id}/approve",
        headers=ADMIN,
        json={"reviewer": "alice"},
    )
    assert approved.status_code == 200
    token = approved.json()["approval_token"]

    allowed = client.post(
        "/v1/agent/act",
        json=_delete_invoice_body(approval_token=token),
    )
    assert allowed.status_code == 200
    assert allowed.json()["decision"] == "allowed"


def test_admin_requires_token():
    assert client.get("/v1/admin/approvals").status_code == 401


def test_audit_and_models_and_explain():
    client.post("/v1/chat", json={
        "model": "gpt-4o-mini-eu",
        "prompt": "hello",
        "caller": "cloth-shop-agent",
        "environment": "dev",
        "data_class": "internal",
    })
    audit = client.get("/v1/admin/audit", headers=ADMIN, params={"caller": "cloth-shop-agent"})
    assert audit.status_code == 200
    assert audit.json()["items"]

    models = client.get("/v1/admin/models", headers=ADMIN)
    assert models.status_code == 200
    ids = {m["id"] for m in models.json()["items"]}
    assert "gpt-4o-mini-eu" in ids

    explained = client.post(
        "/v1/admin/explain",
        headers=ADMIN,
        json={
            "agent_id": "spice-invoice-agent",
            "tool": "delete_invoice",
            "model": "gpt-4o-mini-eu",
            "purpose": "supplier_price_check",
            "lawful_basis": "contract",
            "environment": "prod",
            "data_class": "internal",
            "caller": "team-a",
        },
    )
    assert explained.status_code == 200
    body = explained.json()
    assert body["decision"] == "denied:human_approval_required"
    assert any(c["rule"] == "human_approval_required" and not c["passed"] for c in body["checks"])
