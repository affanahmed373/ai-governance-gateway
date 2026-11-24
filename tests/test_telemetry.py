from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import telemetry
from app.main import app
from app.telemetry import get_memory_exporter, setup_telemetry


def setup_function() -> None:
    # Reset provider so each test owns an in-memory exporter.
    telemetry._configured = False
    telemetry._tracer = None
    setup_telemetry(use_memory_exporter=True)


def test_policy_decision_emits_span_with_rule_id():
    client = TestClient(app)
    response = client.post(
        "/v1/agent/act",
        json={
            "agent_id": "cloth-catalog-agent",
            "tool": "draft_caption",
            "model": "gpt-4o-mini-eu",
            "prompt": "post about coats",
            "purpose": "catalog_post",
            "environment": "dev",
            "data_class": "public",
            "caller": "shop-staff",
            "target_agent": "spice-invoice-agent",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "target_agent_not_allowed"

    exporter = get_memory_exporter()
    assert isinstance(exporter, InMemorySpanExporter)
    spans = exporter.get_finished_spans()
    policy_spans = [s for s in spans if s.name == "policy.decision"]
    assert policy_spans, "expected a policy.decision span"
    span = policy_spans[-1]
    assert span.attributes["governance.rule"] == "target_agent_not_allowed"
    assert span.attributes["governance.decision"] == "denied:target_agent_not_allowed"
    assert span.attributes["governance.agent_id"] == "cloth-catalog-agent"
    assert "prompt" not in span.attributes
    assert span.status.status_code == trace.StatusCode.ERROR


def test_allowed_chat_span_is_ok():
    client = TestClient(app)
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini-eu",
            "prompt": "hello",
            "caller": "cloth-shop-agent",
            "environment": "dev",
            "data_class": "internal",
        },
    )
    assert response.status_code == 200
    exporter = get_memory_exporter()
    assert exporter is not None
    spans = [s for s in exporter.get_finished_spans() if s.name == "policy.decision"]
    assert spans
    span = spans[-1]
    assert span.attributes["governance.decision"] == "allowed"
    assert span.attributes["governance.rule"] == "allowed"
    assert span.status.status_code == trace.StatusCode.OK
