from fastapi.testclient import TestClient


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("GATEWAY_RATE_LIMIT_PER_MINUTE", "3")
    from app import rate_limit
    from app.main import app

    rate_limit.limiter.reset()
    client = TestClient(app)
    body = {
        "model": "gpt-4o-mini-eu",
        "prompt": "hello",
        "environment": "dev",
        "data_class": "internal",
        "caller": "rate-limit-test",
    }
    assert client.post("/v1/chat", json=body).status_code == 200
    assert client.post("/v1/chat", json=body).status_code == 200
    assert client.post("/v1/chat", json=body).status_code == 200
    blocked = client.post("/v1/chat", json=body)
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "rate_limit_exceeded"
    assert blocked.headers.get("retry-after") == "60"
    # Health stays available while the budget is spent.
    assert client.get("/health").status_code == 200
    rate_limit.limiter.reset()


def test_oversized_prompt_rejected(monkeypatch):
    monkeypatch.setenv("GATEWAY_MAX_PROMPT_CHARS", "256")
    monkeypatch.setenv("GATEWAY_RATE_LIMIT_PER_MINUTE", "0")
    # Re-import would not rebuild Field defaults; call the helper and post a long body.
    from app.main import app
    from app.rate_limit import limiter, max_prompt_chars

    limiter.reset()
    client = TestClient(app)
    limit = max_prompt_chars()
    assert limit == 256
    too_long = "x" * (limit + 1)
    response = client.post(
        "/v1/chat",
        json={
            "model": "gpt-4o-mini-eu",
            "prompt": too_long,
            "environment": "dev",
            "data_class": "internal",
            "caller": "size-test",
        },
    )
    assert response.status_code == 422


def test_rate_limit_disabled_with_zero(monkeypatch):
    monkeypatch.setenv("GATEWAY_RATE_LIMIT_PER_MINUTE", "0")
    from app import rate_limit
    from app.main import app

    rate_limit.limiter.reset()
    client = TestClient(app)
    body = {
        "model": "gpt-4o-mini-eu",
        "prompt": "hello",
        "environment": "dev",
        "data_class": "internal",
        "caller": "unlimited-test",
    }
    for _ in range(5):
        assert client.post("/v1/chat", json=body).status_code == 200
    rate_limit.limiter.reset()


def test_default_rate_limit_env(monkeypatch):
    monkeypatch.delenv("GATEWAY_RATE_LIMIT_PER_MINUTE", raising=False)
    from app.rate_limit import rate_limit_per_minute

    assert rate_limit_per_minute() == 30
