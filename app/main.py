import hashlib
import json
import logging
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent_policy import check_agent_action, load_agent_policy
from app.guardrails import detect_prompt_injection, mask_pii
from app.policy import check_model_access, load_registry

app = FastAPI(title="AI Governance Gateway")
audit_log = logging.getLogger("audit")
registry = load_registry()
agent_policy = load_agent_policy()


class ChatRequest(BaseModel):
    model: str
    prompt: str
    environment: str = "dev"
    data_class: str = "internal"
    caller: str = "anonymous"  # TODO: derive from validated Entra ID token


class AgentActionRequest(BaseModel):
    agent_id: str
    tool: str
    model: str
    prompt: str
    purpose: str
    lawful_basis: str | None = None
    environment: str = "dev"
    data_class: str = "internal"
    caller: str = "anonymous"  # TODO: derive from validated Entra ID token
    human_approved: bool = False
    step: int = 1
    target_agent: str | None = None


def write_audit(
    request_id: str,
    req: ChatRequest | AgentActionRequest,
    decision: str,
    rule: str | None = None,
) -> dict:
    record = {
        "request_id": request_id,
        "caller": req.caller,
        "model": req.model,
        "environment": req.environment,
        "data_class": req.data_class,
        "decision": decision,
        "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
    }
    if isinstance(req, AgentActionRequest):
        record["agent_id"] = req.agent_id
        record["tool"] = req.tool
        record["purpose"] = req.purpose
        record["rule"] = rule if rule is not None else decision
    audit_log.info(json.dumps(record))
    return record


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/chat")
def chat(req: ChatRequest) -> dict:
    request_id = str(uuid.uuid4())
    allowed, reason = check_model_access(req.model, req.environment, req.data_class, registry)
    if not allowed:
        write_audit(request_id, req, f"denied:{reason}")
        raise HTTPException(status_code=403, detail=reason)
    if detect_prompt_injection(req.prompt):
        write_audit(request_id, req, "denied:prompt_injection")
        raise HTTPException(status_code=400, detail="prompt_injection_detected")
    safe_prompt = mask_pii(req.prompt)
    write_audit(request_id, req, "allowed")
    # TODO: call the real backend (Azure OpenAI / Ollama) with safe_prompt
    return {"request_id": request_id, "response": f"[stub] would call {req.model}", "masked_prompt": safe_prompt}


@app.post("/v1/agent/act")
def agent_act(req: AgentActionRequest) -> dict:
    request_id = str(uuid.uuid4())
    model = registry.get(req.model)
    model_region = model.get("region") if model else None
    allowed, reason = check_agent_action(
        req.agent_id,
        req.tool,
        req.environment,
        req.data_class,
        req.purpose,
        req.lawful_basis,
        req.human_approved,
        req.step,
        req.caller,
        req.target_agent,
        model_region,
        agent_policy,
    )
    if not allowed:
        write_audit(request_id, req, f"denied:{reason}", rule=reason)
        raise HTTPException(status_code=403, detail=reason)
    allowed, reason = check_model_access(req.model, req.environment, req.data_class, registry)
    if not allowed:
        write_audit(request_id, req, f"denied:{reason}", rule=reason)
        raise HTTPException(status_code=403, detail=reason)
    if detect_prompt_injection(req.prompt):
        write_audit(request_id, req, "denied:prompt_injection", rule="prompt_injection")
        raise HTTPException(status_code=400, detail="prompt_injection_detected")
    safe_prompt = mask_pii(req.prompt)
    write_audit(request_id, req, "allowed", rule="allowed")
    # TODO: call the real backend (Azure OpenAI / Ollama) with safe_prompt, then the tool
    return {
        "request_id": request_id,
        "agent_id": req.agent_id,
        "tool": req.tool,
        "decision": "allowed",
        "response": f"[stub] would call {req.model} for {req.agent_id} via {req.tool}",
        "masked_prompt": safe_prompt,
    }
