from app.policy import check_model_access, load_registry

registry = load_registry()


def test_unapproved_model_blocked():
    ok, reason = check_model_access("experimental-model", "dev", "public", registry)
    assert not ok and reason == "model_not_approved"


def test_unknown_model_blocked():
    ok, reason = check_model_access("nope", "dev", "public", registry)
    assert not ok and reason == "model_not_registered"


def test_data_class_limit():
    ok, reason = check_model_access("gpt-4o-mini-eu", "prod", "confidential", registry)
    assert not ok and reason == "data_class_too_high"


def test_allowed():
    ok, _ = check_model_access("gpt-4o-mini-eu", "prod", "internal", registry)
    assert ok
