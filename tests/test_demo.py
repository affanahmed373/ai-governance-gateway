from fastapi.testclient import TestClient

from app.demo_examples import (
    ALLOWED_A2A,
    ALLOWED_AGENT_ACTION,
    DENIED_A2A,
    DENIED_AGENT_ACTION,
)
from app.main import app

client = TestClient(app)


def test_root_redirects_to_docs():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {307, 302}
    assert response.headers["location"] == "/docs"


def test_docs_examples_allow_and_deny_agent_act():
    allowed = client.post("/v1/agent/act", json=ALLOWED_AGENT_ACTION)
    assert allowed.status_code == 200
    assert allowed.json()["decision"] == "allowed"

    denied = client.post("/v1/agent/act", json=DENIED_AGENT_ACTION)
    assert denied.status_code == 403
    assert denied.json()["detail"] == "target_agent_not_allowed"


def test_docs_examples_allow_and_deny_a2a():
    allowed = client.post("/v1/a2a", json=ALLOWED_A2A)
    assert allowed.status_code == 200
    assert allowed.json()["result"]["task"]["metadata"]["rule"] == "allowed"

    denied = client.post("/v1/a2a", json=DENIED_A2A)
    assert denied.status_code == 200
    task = denied.json()["result"]["task"]
    assert task["status"]["state"] == "TASK_STATE_REJECTED"
    assert task["metadata"]["rule"] == "target_agent_not_allowed"


def test_openapi_lists_allow_and_deny_examples():
    schema = client.get("/openapi.json").json()
    agent_examples = schema["paths"]["/v1/agent/act"]["post"]["requestBody"]["content"][
        "application/json"
    ]["examples"]
    assert "allowed_spice_price_check" in agent_examples
    assert "denied_peer_not_allowed" in agent_examples
    assert (
        agent_examples["denied_peer_not_allowed"]["value"]["target_agent"]
        == "spice-invoice-agent"
    )

    a2a_examples = schema["paths"]["/v1/a2a"]["post"]["requestBody"]["content"][
        "application/json"
    ]["examples"]
    assert "allowed_catalog_draft" in a2a_examples
    assert "denied_peer_not_allowed" in a2a_examples
