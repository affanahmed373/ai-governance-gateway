import pytest

from app.rate_limit import limiter


@pytest.fixture(autouse=True)
def _demo_limits_for_tests(monkeypatch):
    """Keep the suite under the public rate budget unless a test sets its own."""
    monkeypatch.setenv("GATEWAY_RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("GATEWAY_MAX_PROMPT_CHARS", "4000")
    monkeypatch.setenv("OTEL_CONSOLE_EXPORTER", "0")
    limiter.reset()
    yield
    limiter.reset()
