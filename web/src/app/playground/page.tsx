"use client";

import { useState } from "react";

import {
  type AgentActionBody,
  type ExplainCheck,
  agentAct,
  explainAction,
  pendingApprovalIdFromDeny,
} from "@/lib/gateway";

const DEFAULT: AgentActionBody = {
  agent_id: "spice-invoice-agent",
  tool: "delete_invoice",
  model: "gpt-4o-mini-eu",
  prompt: "Delete supplier invoice INV-42 after the PG Tips price check.",
  purpose: "supplier_price_check",
  lawful_basis: "contract",
  environment: "prod",
  data_class: "internal",
  caller: "team-a",
};

export default function PlaygroundPage() {
  const [form, setForm] = useState<AgentActionBody>(DEFAULT);
  const [checks, setChecks] = useState<ExplainCheck[]>([]);
  const [decision, setDecision] = useState<string | null>(null);
  const [actResult, setActResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof AgentActionBody>(key: K, value: AgentActionBody[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onExplain() {
    setError(null);
    try {
      const result = await explainAction(form);
      setDecision(result.decision);
      setChecks(result.checks);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function onAct() {
    setError(null);
    try {
      const result = await agentAct(form);
      if (result.ok) {
        setActResult(`allowed — ${JSON.stringify(result.data)}`);
      } else {
        const pending = pendingApprovalIdFromDeny(result.data);
        setActResult(
          pending
            ? `denied — queued as ${pending}. Open Approvals to mint a token.`
            : `denied — ${JSON.stringify(result.data)}`,
        );
      }
      const explained = await explainAction(form);
      setDecision(explained.decision);
      setChecks(explained.checks);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <>
      <section className="panel">
        <h2>Policy playground</h2>
        <p className="muted">
          Explain shows every rule pass/fail. Act calls the real gate and, for high-impact
          tools, creates a pending approval.
        </p>
        <div className="row" style={{ marginBottom: "0.75rem" }}>
          <input
            value={form.agent_id}
            onChange={(e) => update("agent_id", e.target.value)}
            placeholder="agent_id"
          />
          <input
            value={form.tool}
            onChange={(e) => update("tool", e.target.value)}
            placeholder="tool"
          />
          <input
            value={form.model}
            onChange={(e) => update("model", e.target.value)}
            placeholder="model"
          />
          <input
            value={form.caller}
            onChange={(e) => update("caller", e.target.value)}
            placeholder="caller"
          />
        </div>
        <div className="row" style={{ marginBottom: "0.75rem" }}>
          <input
            value={form.purpose}
            onChange={(e) => update("purpose", e.target.value)}
            placeholder="purpose"
          />
          <input
            value={form.lawful_basis ?? ""}
            onChange={(e) => update("lawful_basis", e.target.value)}
            placeholder="lawful_basis"
          />
          <input
            value={form.environment ?? "dev"}
            onChange={(e) => update("environment", e.target.value)}
            placeholder="environment"
          />
          <input
            value={form.data_class ?? "internal"}
            onChange={(e) => update("data_class", e.target.value)}
            placeholder="data_class"
          />
        </div>
        <textarea
          value={form.prompt}
          onChange={(e) => update("prompt", e.target.value)}
          aria-label="prompt"
        />
        <div className="row" style={{ marginTop: "0.75rem" }}>
          <button type="button" onClick={() => void onExplain()}>
            Explain rules
          </button>
          <button type="button" className="secondary" onClick={() => void onAct()}>
            Run /v1/agent/act
          </button>
        </div>
        {error ? <p className="tag deny">{error}</p> : null}
        {actResult ? <p className="mono">{actResult}</p> : null}
      </section>

      <section className="panel">
        <h2>Rule checklist</h2>
        {decision ? (
          <p>
            Decision:{" "}
            <span className={`tag ${decision === "allowed" ? "allow" : "deny"}`}>
              {decision}
            </span>
          </p>
        ) : (
          <p className="muted">Run Explain or Act to fill this list.</p>
        )}
        <ul className="check-list">
          {checks.map((check) => (
            <li key={check.rule}>
              <span className={`tag ${check.passed ? "allow" : "deny"}`}>
                {check.passed ? "pass" : "fail"}
              </span>
              <div>
                <div className="mono">{check.rule}</div>
                <div className="muted">{check.detail}</div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
