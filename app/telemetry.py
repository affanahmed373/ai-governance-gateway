"""OpenTelemetry spans for policy decisions.

JSON audit lines remain the compliance record. Spans are for operators and
APM backends. See docs/adr/0011-opentelemetry-policy-spans.md.
"""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util._once import Once

_SERVICE_NAME = "ai-governance-gateway"
_tracer: trace.Tracer | None = None
_memory_exporter: InMemorySpanExporter | None = None
_configured = False


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _reset_tracer_provider_for_tests() -> None:
    """The SDK allows only one set_tracer_provider; tests need a fresh provider."""
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE = Once()


def setup_telemetry(*, use_memory_exporter: bool = False) -> None:
    """Configure the global tracer provider once per process (or per test)."""
    global _tracer, _memory_exporter, _configured
    if _configured and not use_memory_exporter:
        return

    if use_memory_exporter or _configured:
        _reset_tracer_provider_for_tests()

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", _SERVICE_NAME),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "0.0.0-dev"),
        }
    )
    provider = TracerProvider(resource=resource)

    if use_memory_exporter:
        _memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_memory_exporter))
    else:
        _memory_exporter = None
        # Console exporter keeps the portfolio demo visible in Container App logs
        # without requiring a collector. Disable with OTEL_CONSOLE_EXPORTER=0.
        if _env_flag("OTEL_CONSOLE_EXPORTER", default=True):
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
        if endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(_SERVICE_NAME)
    _configured = True


def get_memory_exporter() -> InMemorySpanExporter | None:
    return _memory_exporter


def record_policy_decision(record: dict[str, Any]) -> None:
    """Emit one span for a policy decision. Never includes the raw prompt."""
    if _tracer is None:
        setup_telemetry()
    tracer = _tracer
    assert tracer is not None

    decision = str(record.get("decision", ""))
    rule = str(record.get("rule") or decision).removeprefix("denied:")

    with tracer.start_as_current_span("policy.decision") as span:
        span.set_attribute("governance.request_id", str(record.get("request_id", "")))
        span.set_attribute("governance.decision", decision)
        span.set_attribute("governance.rule", rule)
        span.set_attribute("governance.caller", str(record.get("caller", "")))
        span.set_attribute("governance.model", str(record.get("model", "")))
        span.set_attribute("governance.environment", str(record.get("environment", "")))
        span.set_attribute("governance.data_class", str(record.get("data_class", "")))
        if "agent_id" in record:
            span.set_attribute("governance.agent_id", str(record["agent_id"]))
        if "tool" in record:
            span.set_attribute("governance.tool", str(record["tool"]))
        if "purpose" in record:
            span.set_attribute("governance.purpose", str(record["purpose"]))
        if "caller_agent" in record:
            span.set_attribute("governance.caller_agent", str(record["caller_agent"]))
        if "target_agent" in record:
            span.set_attribute("governance.target_agent", str(record["target_agent"]))
        if "prompt_sha256" in record:
            span.set_attribute("governance.prompt_sha256", str(record["prompt_sha256"]))
        if decision.startswith("denied") or decision != "allowed":
            span.set_status(trace.Status(trace.StatusCode.ERROR, rule))
        else:
            span.set_status(trace.Status(trace.StatusCode.OK))
