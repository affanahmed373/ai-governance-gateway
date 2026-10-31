import hashlib
import json
import logging
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.guardrails import detect_prompt_injection, mask_pii
from app.policy import check_model_access, load_registry

app = FastAPI(title="AI Governance Gateway")
audit_log = logging.getLogger("audit")
registry = load_registry()


class ChatRequest(BaseModel):
    model: str
    prompt: str
    environment: str = "dev"
    data_class: str = "internal"
    caller: str = "anonymous"  # TODO: derive from validated Entra ID token


def write_audit(request_id: str, req: ChatRequest, decision: str) -> dict:
    record = {
        "request_id": request_id,
        "caller": req.caller,
        "model": req.model,
        "environment": req.environment,
        "data_class": req.data_class,
        "decision": decision,
        "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
    }
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
