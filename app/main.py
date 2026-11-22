import hashlib
import json
import logging
import os
import sys
import uuid
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, field_validator

from app.a2a import (
    build_agent_card,
    build_gateway_card,
    handle_a2a_request,
    invalid_json_response,
)
from app.agent_policy import check_agent_action, explain_agent_action, load_agent_policy
from app.approval import admin_token, pending_approvals
from app.audit_store import audit_store
from app.demo_examples import A2A_OPENAPI_EXAMPLES, AGENT_ACT_OPENAPI_EXAMPLES
from app.guardrails import detect_prompt_injection, mask_pii
from app.policy import check_model_access, load_registry
from app.rate_limit import RateLimitMiddleware, max_prompt_chars

app = FastAPI(
    title="AI Governance Gateway",
    description=(
        "Rule-based gate for LLM and agent calls. High-impact tools need a "
        "signed `approval_token` from the admin queue (not a boolean flag). "
        "Open **POST /v1/agent/act** for allow/deny demos. Public demo: "
        "30 requests/minute per client and a 4000-character prompt cap."
    ),
)
app.add_middleware(RateLimitMiddleware)

_cors_origins = [
    o.strip()
    for o in os.getenv(
        "GATEWAY_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audit_log = logging.getLogger("audit")
audit_log.setLevel(logging.INFO)
if not audit_log.handlers:
    _audit_handler = logging.StreamHandler(sys.stdout)
    _audit_handler.setFormatter(logging.Formatter("%(message)s"))
    audit_log.addHandler(_audit_handler)
registry = load_registry()
agent_policy = load_agent_policy()


def _prompt_within_cap(value: str) -> str:
    limit = max_prompt_chars()
    if len(value) > limit:
        raise ValueError(f"prompt exceeds GATEWAY_MAX_PROMPT_CHARS ({limit})")
    return value


class ChatRequest(BaseModel):
    model: str
    prompt: str
    environment: str = "dev"
    data_class: str = "internal"
    caller: str = "anonymous"  # TODO: derive from validated Entra ID token

    @field_validator("prompt")
    @classmethod
    def prompt_cap(cls, value: str) -> str:
        return _prompt_within_cap(value)


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
    human_approved: bool = False  # ignored; kept for older clients
    approval_token: str | None = None
    step: int = 1
    target_agent: str | None = None

    @field_validator("prompt")
    @classmethod
    def prompt_cap(cls, value: str) -> str:
        return _prompt_within_cap(value)


class ExplainRequest(BaseModel):
    agent_id: str
    tool: str
    model: str
    purpose: str
    lawful_basis: str | None = None
    environment: str = "dev"
    data_class: str = "internal"
    caller: str = "anonymous"
    approval_token: str | None = None
    step: int = 1
    target_agent: str | None = None


class ReviewerBody(BaseModel):
    reviewer: str = "console-reviewer"


def require_admin(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    if not x_admin_token or not hmac_compare(x_admin_token, admin_token()):
        raise HTTPException(status_code=401, detail="admin_token_required")


def hmac_compare(left: str, right: str) -> bool:
    import hmac as _hmac

    return _hmac.compare_digest(left.encode(), right.encode())


def write_audit(
    request_id: str,
    req: ChatRequest | AgentActionRequest,
    decision: str,
    rule: str | None = None,
    caller_agent: str | None = None,
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
        if req.target_agent is not None:
            record["target_agent"] = req.target_agent
    if caller_agent is not None:
        record["caller_agent"] = caller_agent
    audit_log.info(json.dumps(record))
    audit_store.add(record)
    return record


def _a2a_endpoint(request: Request) -> str:
    return f"{str(request.base_url).rstrip('/')}/v1/a2a"


def _action_snapshot(req: AgentActionRequest) -> dict:
    return {
        "agent_id": req.agent_id,
        "tool": req.tool,
        "model": req.model,
        "prompt": req.prompt,
        "purpose": req.purpose,
        "lawful_basis": req.lawful_basis,
        "environment": req.environment,
        "data_class": req.data_class,
        "caller": req.caller,
        "step": req.step,
        "target_agent": req.target_agent,
    }


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


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
def agent_act(
    req: Annotated[
        AgentActionRequest,
        Body(openapi_examples=AGENT_ACT_OPENAPI_EXAMPLES),
    ],
) -> dict:
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
        approval_token=req.approval_token,
    )
    if not allowed:
        pending_id = None
        if reason == "human_approval_required":
            pending = pending_approvals.enqueue(_action_snapshot(req))
            pending_id = pending["id"]
        write_audit(request_id, req, f"denied:{reason}", rule=reason)
        detail: dict | str
        if pending_id:
            detail = {"detail": reason, "pending_approval_id": pending_id}
        else:
            detail = reason
        raise HTTPException(status_code=403, detail=detail)
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


@app.get("/.well-known/agent-card.json")
@app.get("/v1/a2a/agent-card.json")
def a2a_gateway_card(request: Request) -> dict:
    return build_gateway_card(agent_policy, _a2a_endpoint(request))


@app.get("/v1/a2a/agents/{agent_id}/agent-card.json")
def a2a_agent_card(agent_id: str, request: Request) -> dict:
    card = build_agent_card(agent_id, agent_policy, _a2a_endpoint(request))
    if card is None:
        raise HTTPException(status_code=404, detail="agent_not_registered")
    return card


@app.post(
    "/v1/a2a",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": A2A_OPENAPI_EXAMPLES,
                }
            },
        }
    },
)
async def a2a(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        outcome = invalid_json_response()
    else:
        outcome = handle_a2a_request(body, agent_policy, registry)
    audit = outcome["audit"]
    if audit is not None:
        recorded = AgentActionRequest(
            agent_id=audit["caller_agent"],
            tool=audit["tool"],
            model=audit["model"],
            prompt=audit["prompt"],
            purpose=audit["purpose"],
            environment=audit["environment"],
            data_class=audit["data_class"],
            caller=audit["caller"],
            target_agent=audit["target_agent"],
            approval_token=audit.get("approval_token"),
        )
        write_audit(
            audit["request_id"],
            recorded,
            audit["decision"],
            rule=audit["rule"],
            caller_agent=audit["caller_agent"],
        )
    return JSONResponse(outcome["response"], status_code=outcome["http_status"])


@app.get("/v1/admin/approvals", dependencies=[Depends(require_admin)])
def list_approvals() -> dict:
    return {"items": pending_approvals.list_pending()}


@app.post("/v1/admin/approvals/{approval_id}/approve", dependencies=[Depends(require_admin)])
def approve_action(approval_id: str, body: ReviewerBody) -> dict:
    item = pending_approvals.approve(approval_id, body.reviewer)
    if item is None:
        raise HTTPException(status_code=404, detail="approval_not_found")
    return {
        "id": item["id"],
        "status": item["status"],
        "approval_token": item["approval_token"],
        "expires_at": item["expires_at"],
        "action": item["action"],
    }


@app.post("/v1/admin/approvals/{approval_id}/reject", dependencies=[Depends(require_admin)])
def reject_action(approval_id: str, body: ReviewerBody) -> dict:
    item = pending_approvals.reject(approval_id, body.reviewer)
    if item is None:
        raise HTTPException(status_code=404, detail="approval_not_found")
    return {"id": item["id"], "status": item["status"]}


@app.get("/v1/admin/audit", dependencies=[Depends(require_admin)])
def list_audit(
    caller: str | None = None,
    agent_id: str | None = None,
    rule: str | None = None,
    decision: str | None = None,
    limit: int = 50,
) -> dict:
    return {
        "items": audit_store.list(
            caller=caller,
            agent_id=agent_id,
            rule=rule,
            decision=decision,
            limit=limit,
        )
    }


@app.get("/v1/admin/models", dependencies=[Depends(require_admin)])
def list_models() -> dict:
    return {
        "items": [
            {
                "id": model_id,
                "provider": meta.get("provider"),
                "region": meta.get("region"),
                "status": meta.get("status"),
                "max_data_class": meta.get("max_data_class"),
                "environments": meta.get("environments"),
            }
            for model_id, meta in registry.items()
        ]
    }


@app.post("/v1/admin/explain", dependencies=[Depends(require_admin)])
def explain_action(req: ExplainRequest) -> dict:
    model = registry.get(req.model)
    model_region = model.get("region") if model else None
    checks = explain_agent_action(
        req.agent_id,
        req.tool,
        req.environment,
        req.data_class,
        req.purpose,
        req.lawful_basis,
        req.step,
        req.caller,
        req.target_agent,
        model_region,
        agent_policy,
        approval_token=req.approval_token,
    )
    model_ok, model_reason = check_model_access(
        req.model, req.environment, req.data_class, registry
    )
    checks.append(
        {
            "rule": model_reason if not model_ok else "model_allowed",
            "passed": model_ok,
            "detail": "Approved-model registry check",
        }
    )
    first_fail = next((c["rule"] for c in checks if not c["passed"]), None)
    return {
        "decision": "allowed" if first_fail is None else f"denied:{first_fail}",
        "checks": checks,
    }
