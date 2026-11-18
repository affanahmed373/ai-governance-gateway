"""Ready-made request bodies for /docs and the public demo."""

ALLOWED_AGENT_ACTION = {
    "agent_id": "spice-invoice-agent",
    "tool": "compare_prices",
    "model": "gpt-4o-mini-eu",
    "prompt": "Which vendor has the cheaper price for PG Tips tea bags?",
    "purpose": "supplier_price_check",
    "lawful_basis": "contract",
    "environment": "prod",
    "data_class": "internal",
    "caller": "spice-shop-owner",
    "human_approved": False,
    "step": 1,
}

DENIED_AGENT_ACTION = {
    "agent_id": "cloth-catalog-agent",
    "tool": "draft_caption",
    "model": "gpt-4o-mini-eu",
    "prompt": "Which vendor has the cheaper price for PG Tips tea bags?",
    "purpose": "catalog_post",
    "lawful_basis": "contract",
    "environment": "prod",
    "data_class": "public",
    "caller": "cloth-shop-owner",
    "human_approved": False,
    "step": 1,
    "target_agent": "spice-invoice-agent",
}

ALLOWED_A2A = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "SendMessage",
    "params": {
        "tenant": "cloth-catalog-agent",
        "message": {
            "messageId": "m-allow",
            "role": "ROLE_USER",
            "parts": [{"text": "Draft an Instagram caption for the green waistcoat."}],
        },
        "metadata": {
            "caller_agent": "cloth-shop-agent",
            "tool": "draft_caption",
            "model": "gpt-4o-mini-eu",
            "purpose": "catalog_post",
            "lawful_basis": "contract",
            "environment": "prod",
            "data_class": "internal",
            "caller": "team-a",
        },
    },
}

DENIED_A2A = {
    "jsonrpc": "2.0",
    "id": "2",
    "method": "SendMessage",
    "params": {
        "tenant": "spice-invoice-agent",
        "message": {
            "messageId": "m-block",
            "role": "ROLE_USER",
            "parts": [{"text": "Which vendor has the cheaper price for PG Tips tea bags?"}],
        },
        "metadata": {
            "caller_agent": "cloth-catalog-agent",
            "tool": "draft_caption",
            "model": "gpt-4o-mini-eu",
            "purpose": "catalog_post",
            "environment": "prod",
            "data_class": "public",
            "caller": "team-a",
        },
    },
}

AGENT_ACT_OPENAPI_EXAMPLES = {
    "allowed_spice_price_check": {
        "summary": "Allowed: spice shop compares supplier prices",
        "description": "Returns HTTP 200 with decision allowed.",
        "value": ALLOWED_AGENT_ACTION,
    },
    "denied_peer_not_allowed": {
        "summary": "Denied: target_agent_not_allowed (C-26 / ASI07)",
        "description": (
            "The catalog agent may not call the spice invoice agent. "
            "Expect HTTP 403 with detail target_agent_not_allowed."
        ),
        "value": DENIED_AGENT_ACTION,
    },
}

A2A_OPENAPI_EXAMPLES = {
    "allowed_catalog_draft": {
        "summary": "Allowed: cloth shop asks catalog agent",
        "description": "Task state TASK_STATE_COMPLETED, rule allowed.",
        "value": ALLOWED_A2A,
    },
    "denied_peer_not_allowed": {
        "summary": "Denied: target_agent_not_allowed (C-26 / ASI07)",
        "description": (
            "Task state TASK_STATE_REJECTED with "
            "result.task.metadata.rule = target_agent_not_allowed."
        ),
        "value": DENIED_A2A,
    },
}
