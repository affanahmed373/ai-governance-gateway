# Roadmap

Planned improvements. Each item lists the skill it proves and what "done" means.
Add the skill to the CV only after the item is pushed.

## Frontend showcase and hosting
- Frontend: **TypeScript showcase.** Next.js (TypeScript) admin console in `web/` (section 2c). The FastAPI gateway stays Python; the console reads TypeScript types generated from its OpenAPI schema.
- Demo hosting: console on Vercel (Hobby plan, free for personal projects); API on a Hugging Face Docker Space (section 2b).
- Cloud: Azure Container Apps on the consumption plan with minimum replicas 0, as in ADR 0003, so nothing is billed while idle.

## 1. Govern A2A calls (priority: medium)
Proves: A2A protocol in public code.
- [x] Accept A2A agent-to-agent requests (agent card + task messages) on a new endpoint.
- [x] Apply the existing `check_agent_action` rules (data class, lawful basis, region, human approval) to each A2A task.
- [x] Audit-log caller agent, target agent and decision.
Done when: a demo with two small agents shows one A2A call allowed and one blocked.

## 2. Use it in front of a real agent (priority: high)
Proves: the gateway works on real traffic, not just tests.
- [x] Route `multi-cloud-retail-agent` LLM calls through the gateway (`/chat`) and show the audit log in the README.

## 2b. Live demo (priority: high)
Proves: the policy engine can be tried, not only read.
- [ ] Add a `Dockerfile` (port 7860) and deploy to a Hugging Face Docker Space; no LLM key needed for the policy checks.
- [ ] Open on the FastAPI `/docs` page with two ready example requests: one action allowed, one denied with the rule id from the control matrix.
- [ ] "Try it" link and a screenshot of a denied request at the top of the README.
Done when: a visitor sees an allow and a deny within one minute.

## 2c. TypeScript admin console (priority: high)
Proves: TypeScript (Next.js) in public code, and a human approval step that is enforced, not declared.
- [ ] Next.js App Router + TypeScript in `web/`; API types generated from the FastAPI OpenAPI schema (`openapi-typescript`).
- [ ] Approval queue: a reviewer approves or rejects a pending high-impact action; approval issues a signed token that `POST /v1/agent/act` verifies.
- [ ] Audit log viewer with filters (caller, agent, rule id, decision), approved-model list, and a playground that runs an action and shows each rule's allow or deny.
- [ ] Vitest unit tests, one Playwright test, and a CI job for type-check, lint and tests.
- [ ] Deploy to Vercel; API base URL from an environment variable; CORS on the API allows only the Vercel domain.
Done when: on the Vercel link, an action is denied, a reviewer approves it in the queue, and the retried action passes.

## 3. OpenTelemetry audit trail (priority: medium)
Proves: OpenTelemetry, enterprise observability.
- [ ] Emit each policy decision as an OpenTelemetry span with the rule id from the control matrix.
- [ ] Keep the JSON audit log as the compliance record.

## 4. Stronger guardrails (priority: low)
- [ ] Add an ML-based prompt-injection classifier next to the pattern rules and report precision/recall on a small labelled set.
