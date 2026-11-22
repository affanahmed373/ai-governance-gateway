from pathlib import Path

import yaml

from app.approval import verify_approval_token
from app.policy import DATA_CLASS_ORDER

POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "agent_policy.yaml"


def load_agent_policy(path: Path = POLICY_PATH) -> dict:
    data = yaml.safe_load(path.read_text())
    return {
        "agents": {item["id"]: item for item in data["agents"]},
        "tools": {item["id"]: item for item in data["tools"]},
        "prohibited_purposes": data["prohibited_purposes"],
        "lawful_bases": data["lawful_bases"],
        "allowed_regions": data["allowed_regions"],
    }


def check_agent_action(
    agent_id: str,
    tool_id: str,
    environment: str,
    data_class: str,
    purpose: str,
    lawful_basis: str | None,
    human_approved: bool,
    step: int,
    caller: str,
    target_agent: str | None,
    model_region: str | None,
    policy: dict,
    approval_token: str | None = None,
) -> tuple[bool, str]:
    """Return (allowed, reason). `human_approved` is ignored; a signed token is required."""
    del human_approved  # kept on the HTTP/A2A surface for older clients; not trusted
    for check in explain_agent_action(
        agent_id,
        tool_id,
        environment,
        data_class,
        purpose,
        lawful_basis,
        step,
        caller,
        target_agent,
        model_region,
        policy,
        approval_token,
    ):
        if not check["passed"]:
            return False, check["rule"]
    return True, "allowed"


def explain_agent_action(
    agent_id: str,
    tool_id: str,
    environment: str,
    data_class: str,
    purpose: str,
    lawful_basis: str | None,
    step: int,
    caller: str,
    target_agent: str | None,
    model_region: str | None,
    policy: dict,
    approval_token: str | None = None,
) -> list[dict]:
    """Run every agent rule and return pass/fail for the admin playground."""
    checks: list[dict] = []
    agent = policy["agents"].get(agent_id)
    tools = policy["tools"]

    def add(rule: str, passed: bool, detail: str) -> None:
        checks.append({"rule": rule, "passed": passed, "detail": detail})

    add(
        "agent_not_registered",
        agent is not None,
        "Agent must appear in config/agent_policy.yaml",
    )
    if agent is None:
        return checks

    add(
        "agent_not_approved",
        agent["status"] == "approved",
        f"Agent status is {agent['status']!r}",
    )
    add(
        "environment_not_allowed",
        environment in agent["environments"],
        f"Allowed environments: {agent['environments']}",
    )
    add(
        "purpose_prohibited",
        purpose not in policy["prohibited_purposes"],
        "Purpose is not on the global prohibited list",
    )
    add(
        "purpose_not_allowed",
        purpose in agent["purposes"],
        f"Agent purposes: {agent['purposes']}",
    )
    known_class = data_class in DATA_CLASS_ORDER
    add("unknown_data_class", known_class, f"Known classes: {list(DATA_CLASS_ORDER)}")
    if known_class:
        add(
            "lawful_basis_required",
            data_class == "public" or lawful_basis in policy["lawful_bases"],
            "Non-public data needs a GDPR Art. 6(1) basis",
        )
        add(
            "special_category_denied",
            data_class != "restricted",
            "restricted is denied for every agent",
        )
        add(
            "data_class_too_high",
            DATA_CLASS_ORDER.index(data_class)
            <= DATA_CLASS_ORDER.index(agent["max_data_class"]),
            f"Agent max_data_class is {agent['max_data_class']}",
        )
    named_caller = (caller or "").strip()
    add(
        "caller_required",
        bool(named_caller) and named_caller.lower() != "anonymous",
        "Caller must be a named identity",
    )
    add(
        "tool_not_allowed",
        tool_id in agent["allowed_tools"],
        f"Allowed tools: {agent['allowed_tools']}",
    )
    tool = tools.get(tool_id)
    add("tool_not_registered", tool is not None, "Tool must be registered")
    if tool is not None:
        add(
            "code_execution_denied",
            not tool.get("allows_code_execution"),
            "Code-execution tools are denied until a sandbox exists",
        )
        needs_approval = bool(tool.get("requires_human_approval"))
        token_ok = verify_approval_token(
            approval_token,
            agent_id=agent_id,
            tool=tool_id,
            purpose=purpose,
            caller=named_caller or caller,
        )
        add(
            "human_approval_required",
            (not needs_approval) or token_ok,
            "High-impact tool needs a signed approval_token from the admin queue",
        )
    add(
        "step_budget_exceeded",
        1 <= step <= agent["max_steps"],
        f"Step must be 1..{agent['max_steps']}",
    )
    add(
        "target_agent_not_allowed",
        target_agent is None or target_agent in agent["allowed_peers"],
        f"Allowed peers: {agent['allowed_peers']}",
    )
    if known_class:
        add(
            "region_not_allowed",
            data_class == "public" or model_region in policy["allowed_regions"],
            f"Allowed regions: {policy['allowed_regions']}",
        )
    return checks
