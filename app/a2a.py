import uuid
from datetime import UTC, datetime

from app.agent_policy import check_agent_action
from app.guardrails import detect_prompt_injection, mask_pii
from app.policy import check_model_access
from app.rate_limit import max_prompt_chars

PROTOCOL_VERSION = "1.0"
EXTENSION_URI = "https://github.com/affanahmed373/ai-governance-gateway/a2a/governance/v1"

_INVALID_REQUEST = -32600
_METHOD_NOT_FOUND = -32601
_INVALID_PARAMS = -32602
_PARSE_ERROR = -32700


def build_gateway_card(policy: dict, endpoint_url: str) -> dict:
    skills = [
        {
            "id": agent_id,
            "name": agent_id,
            "description": _agent_summary(agent),
            "tags": ["agent", agent["status"]],
        }
        for agent_id, agent in policy["agents"].items()
    ]
    return _card(
        "AI Governance Gateway",
        "Governed entry point for agent-to-agent tasks. "
        "Set tenant to the target agent and metadata.caller_agent to the caller.",
        endpoint_url,
        skills,
        tenant=None,
    )


def build_agent_card(agent_id: str, policy: dict, endpoint_url: str) -> dict | None:
    agent = policy["agents"].get(agent_id)
    if agent is None:
        return None
    skills = []
    for tool_id in agent["allowed_tools"]:
        tool = policy["tools"].get(tool_id, {})
        description = f"Side effect: {tool.get('side_effect', 'unknown')}."
        if tool.get("requires_human_approval"):
            description += " Human approval required."
        if tool.get("allows_code_execution"):
            description += " Code execution is denied."
        skills.append(
            {
                "id": tool_id,
                "name": tool_id,
                "description": description,
                "tags": [tool_id, tool.get("side_effect", "unknown")],
                "inputModes": ["text/plain"],
                "outputModes": ["text/plain"],
            }
        )
    return _card(agent_id, _agent_summary(agent), endpoint_url, skills, tenant=agent_id)


def invalid_json_response() -> dict:
    return _failure(None, _PARSE_ERROR, "Invalid JSON payload")


def handle_a2a_request(body: object, policy: dict, registry: dict) -> dict:
    if not isinstance(body, dict):
        return _failure(None, _INVALID_REQUEST, "Request payload validation error")
    req_id = body.get("id")
    if body.get("jsonrpc") != "2.0" or "method" not in body:
        return _failure(req_id, _INVALID_REQUEST, "Request payload validation error")
    if body.get("method") != "SendMessage":
        return _failure(req_id, _METHOD_NOT_FOUND, "Method not found")

    params = body.get("params")
    if not isinstance(params, dict):
        return _failure(req_id, _INVALID_PARAMS, "Invalid parameters")
    message = params.get("message")
    if not isinstance(message, dict):
        return _failure(req_id, _INVALID_PARAMS, "Invalid parameters")
    if not message.get("messageId") or message.get("role") not in {"ROLE_USER", "ROLE_AGENT"}:
        return _failure(req_id, _INVALID_PARAMS, "Invalid parameters")
    try:
        prompt = _prompt_from_parts(message.get("parts"))
        fields = _governance_fields(params, params.get("metadata", {}))
    except (TypeError, ValueError):
        return _failure(req_id, _INVALID_PARAMS, "Invalid parameters")
    if len(prompt) > max_prompt_chars():
        return _failure(req_id, _INVALID_PARAMS, "prompt exceeds size limit")

    context_id = message.get("contextId")
    if not isinstance(context_id, str) or not context_id.strip():
        context_id = str(uuid.uuid4())
    return _govern(req_id, prompt, fields, context_id, policy, registry)


def _card(name: str, description: str, endpoint_url: str, skills: list, tenant: str | None) -> dict:
    interface = {
        "url": endpoint_url,
        "protocolBinding": "JSONRPC",
        "protocolVersion": PROTOCOL_VERSION,
    }
    if tenant is not None:
        interface["tenant"] = tenant
    return {
        "name": name,
        "description": description,
        "supportedInterfaces": [interface],
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "extendedAgentCard": False,
            "extensions": [
                {
                    "uri": EXTENSION_URI,
                    "description": (
                        "Governance fields on SendMessage metadata: caller_agent, tool, "
                        "model, purpose, lawful_basis, data_class, caller, "
                        "human_approved, step."
                    ),
                    "required": False,
                }
            ],
        },
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": skills,
    }


def _agent_summary(agent: dict) -> str:
    peers = ", ".join(agent["allowed_peers"]) or "none"
    purposes = ", ".join(agent["purposes"])
    return f"Status {agent['status']}. Purposes: {purposes}. Peers: {peers}."


def _prompt_from_parts(parts: object) -> str:
    if not isinstance(parts, list):
        raise TypeError("parts")
    if not parts:
        raise ValueError("parts")
    texts = []
    for part in parts:
        if not isinstance(part, dict):
            raise TypeError("part")
        if "text" in part:
            if not isinstance(part["text"], str):
                raise TypeError("text")
            texts.append(part["text"])
        elif not any(key in part for key in ("raw", "url", "data")):
            raise ValueError("part")
    return "\n".join(texts)


def _governance_fields(params: dict, metadata: object) -> dict:
    if not isinstance(metadata, dict):
        raise TypeError("metadata")
    step = metadata.get("step", 1)
    if type(step) is not int:
        raise TypeError("step")
    human_approved = metadata.get("human_approved", False)
    if not isinstance(human_approved, bool):
        raise TypeError("human_approved")
    target = _optional_str(params, "tenant")
    if target is None or not target.strip():
        target = _optional_str(metadata, "target_agent")
    return {
        "caller_agent": (_optional_str(metadata, "caller_agent") or "").strip(),
        "target_agent": (target or "").strip(),
        "tool": _optional_str(metadata, "tool") or "",
        "model": _optional_str(metadata, "model") or "",
        "purpose": _optional_str(metadata, "purpose") or "",
        "lawful_basis": _optional_str(metadata, "lawful_basis"),
        "environment": _optional_str(metadata, "environment") or "dev",
        "data_class": _optional_str(metadata, "data_class") or "internal",
        "caller": _optional_str(metadata, "caller") or "anonymous",
        "human_approved": human_approved,
        "step": step,
    }


def _optional_str(source: dict, key: str) -> str | None:
    if key not in source or source[key] is None:
        return None
    value = source[key]
    if not isinstance(value, str):
        raise TypeError(key)
    return value


def _govern(
    req_id: object,
    prompt: str,
    fields: dict,
    context_id: str,
    policy: dict,
    registry: dict,
) -> dict:
    request_id = str(uuid.uuid4())
    caller_agent = fields["caller_agent"]
    target_agent = fields["target_agent"]
    if not caller_agent:
        return _decision(req_id, request_id, prompt, fields, context_id, "caller_agent_required")
    if not target_agent:
        return _decision(req_id, request_id, prompt, fields, context_id, "target_agent_required")

    model = registry.get(fields["model"]) if fields["model"] else None
    model_region = model.get("region") if model else None
    allowed, reason = check_agent_action(
        caller_agent,
        fields["tool"],
        fields["environment"],
        fields["data_class"],
        fields["purpose"],
        fields["lawful_basis"],
        fields["human_approved"],
        fields["step"],
        fields["caller"],
        target_agent,
        model_region,
        policy,
    )
    if allowed:
        allowed, reason = check_model_access(
            fields["model"], fields["environment"], fields["data_class"], registry
        )
    if allowed and detect_prompt_injection(prompt):
        reason = "prompt_injection"
        allowed = False
    if not allowed:
        return _decision(req_id, request_id, prompt, fields, context_id, reason)

    safe_prompt = mask_pii(prompt)
    artifact = {
        "artifactId": str(uuid.uuid4()),
        "name": "result",
        "parts": [
            {
                "text": (
                    f"[stub] would call {fields['model']} for {caller_agent} "
                    f"via {fields['tool']}. {safe_prompt}"
                )
            }
        ],
    }
    return _decision(
        req_id,
        request_id,
        prompt,
        fields,
        context_id,
        "allowed",
        artifact=artifact,
    )


def _decision(
    req_id: object,
    request_id: str,
    prompt: str,
    fields: dict,
    context_id: str,
    reason: str,
    artifact: dict | None = None,
) -> dict:
    allowed = reason == "allowed"
    state = "TASK_STATE_COMPLETED" if allowed else "TASK_STATE_REJECTED"
    decision = "allowed" if allowed else "denied"
    task = {
        "id": str(uuid.uuid4()),
        "contextId": context_id,
        "status": {
            "state": state,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "ROLE_AGENT",
                "parts": [{"text": reason if allowed else f"denied:{reason}"}],
            },
        },
        "metadata": {
            "request_id": request_id,
            "rule": reason,
            "decision": decision,
            "caller_agent": fields["caller_agent"],
            "target_agent": fields["target_agent"],
        },
    }
    if artifact is not None:
        task["artifacts"] = [artifact]
    audit = {
        "request_id": request_id,
        "caller": fields["caller"],
        "caller_agent": fields["caller_agent"],
        "target_agent": fields["target_agent"],
        "model": fields["model"],
        "environment": fields["environment"],
        "data_class": fields["data_class"],
        "prompt": prompt,
        "tool": fields["tool"],
        "purpose": fields["purpose"],
        "decision": "allowed" if allowed else f"denied:{reason}",
        "rule": reason,
    }
    return {
        "http_status": 200,
        "response": {"jsonrpc": "2.0", "id": req_id, "result": {"task": task}},
        "audit": audit,
    }


def _failure(req_id: object, code: int, message: str) -> dict:
    return {
        "http_status": 400,
        "response": {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        },
        "audit": None,
    }
