import json
import logging
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_audit_lines_reach_stdout():
    """Container log collectors (Log Analytics) only see what reaches stdout."""
    script = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "TestClient(app).post('/v1/chat', json={'model': 'gpt-4o-mini-eu', "
        "'prompt': 'hi', 'caller': 'cloth-shop-agent'})\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
    record = json.loads(lines[-1])
    assert record["caller"] == "cloth-shop-agent"
    assert record["decision"] == "allowed"
    assert "prompt_sha256" in record


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
