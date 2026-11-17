import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_denied_unapproved_model():
    r = client.post("/v1/chat", json={"model": "experimental-model", "prompt": "hi"})
    assert r.status_code == 403


def test_allowed_request_masks_pii():
    r = client.post("/v1/chat", json={"model": "gpt-4o-mini-eu", "prompt": "mail me at a@b.com"})
    assert r.status_code == 200
    assert "[EMAIL]" in r.json()["masked_prompt"]


def test_cloth_shop_chat_audit_log(caplog):
    """Retail agent traffic: caller cloth-shop-agent, hash only, decision allowed."""
    caplog.set_level(logging.INFO, logger="audit")
    prompt = "Do you ship the green waistcoat to Berlin? mail me at buyer@example.com"
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini-eu",
            "prompt": prompt,
            "environment": "dev",
            "data_class": "internal",
            "caller": "cloth-shop-agent",
        },
    )
    assert response.status_code == 200
    assert "[EMAIL]" in response.json()["masked_prompt"]
    assert prompt not in caplog.text
    record = json.loads(caplog.records[-1].message)
    assert record["caller"] == "cloth-shop-agent"
    assert record["model"] == "gpt-4o-mini-eu"
    assert record["decision"] == "allowed"
    assert "prompt_sha256" in record
    assert "prompt" not in record
