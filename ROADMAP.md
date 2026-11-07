# Roadmap

Planned improvements. Each item lists the skill it proves and what "done" means.
Add the skill to the CV only after the item is pushed.

## 1. Govern A2A calls (priority: medium)
Proves: A2A protocol in public code.
- [ ] Accept A2A agent-to-agent requests (agent card + task messages) on a new endpoint.
- [ ] Apply the existing `check_agent_action` rules (data class, lawful basis, region, human approval) to each A2A task.
- [ ] Audit-log caller agent, target agent and decision.
Done when: a demo with two small agents shows one A2A call allowed and one blocked.

## 2. Use it in front of a real agent (priority: high)
Proves: the gateway works on real traffic, not just tests.
- [ ] Route `multi-cloud-retail-agent` LLM calls through the gateway (`/chat`) and show the audit log in the README.

## 3. OpenTelemetry audit trail (priority: medium)
Proves: OpenTelemetry, enterprise observability.
- [ ] Emit each policy decision as an OpenTelemetry span with the rule id from the control matrix.
- [ ] Keep the JSON audit log as the compliance record.

## 4. Stronger guardrails (priority: low)
- [ ] Add an ML-based prompt-injection classifier next to the pattern rules and report precision/recall on a small labelled set.
