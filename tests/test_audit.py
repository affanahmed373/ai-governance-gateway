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
