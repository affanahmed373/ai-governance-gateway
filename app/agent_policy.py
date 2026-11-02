from pathlib import Path

import yaml

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
) -> tuple[bool, str]:
    agent = policy["agents"].get(agent_id)
    if agent is None:
        return False, "agent_not_registered"
    if agent["status"] != "approved":
        return False, "agent_not_approved"
    if environment not in agent["environments"]:
        return False, "environment_not_allowed"
    if purpose in policy["prohibited_purposes"]:
        return False, "purpose_prohibited"
    if purpose not in agent["purposes"]:
        return False, "purpose_not_allowed"
    if data_class not in DATA_CLASS_ORDER:
        return False, "unknown_data_class"
    if data_class != "public" and lawful_basis not in policy["lawful_bases"]:
        return False, "lawful_basis_required"
    if data_class == "restricted":
        return False, "special_category_denied"
    if DATA_CLASS_ORDER.index(data_class) > DATA_CLASS_ORDER.index(agent["max_data_class"]):
        return False, "data_class_too_high"
    named_caller = (caller or "").strip()
    if not named_caller or named_caller.lower() == "anonymous":
        return False, "caller_required"
    if tool_id not in agent["allowed_tools"]:
        return False, "tool_not_allowed"
    tool = policy["tools"].get(tool_id)
    if tool is None:
        return False, "tool_not_registered"
    if tool.get("allows_code_execution"):
        return False, "code_execution_denied"
    if tool.get("requires_human_approval") and not human_approved:
        return False, "human_approval_required"
    if step < 1 or step > agent["max_steps"]:
        return False, "step_budget_exceeded"
    if target_agent and target_agent not in agent["allowed_peers"]:
        return False, "target_agent_not_allowed"
    if data_class != "public" and model_region not in policy["allowed_regions"]:
        return False, "region_not_allowed"
    return True, "allowed"
