"use client";

import Link from "next/link";
import { useState } from "react";

import { HowToGuide } from "@/components/HowToGuide";
import {
  type AgentActionBody,
  type ExplainCheck,
  agentAct,
  explainAction,
  pendingApprovalIdFromDeny,
} from "@/lib/gateway";
import { SCENARIOS } from "@/lib/scenarios";

export default function PlaygroundPage() {
  const [scenarioId, setScenarioId] = useState(SCENARIOS[0].id);
  const [form, setForm] = useState<AgentActionBody>(SCENARIOS[0].body);
  const [checks, setChecks] = useState<ExplainCheck[]>([]);
  const [decision, setDecision] = useState<string | null>(null);
  const [actResult, setActResult] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const scenario = SCENARIOS.find((s) => s.id === scenarioId) ?? SCENARIOS[0];

  function pickScenario(id: string) {
    const next = SCENARIOS.find((s) => s.id === id) ?? SCENARIOS[0];
    setScenarioId(next.id);
    setForm(next.body);
    setActResult(null);
    setPendingId(null);
    setDecision(null);
    setChecks([]);
    setError(null);
  }

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
    setPendingId(null);
    try {
      const result = await agentAct(form);
      if (result.ok) {
        setActResult("Allowed. No approval needed for this action.");
        setPendingId(null);
      } else {
        const pending = pendingApprovalIdFromDeny(result.data);
        if (pending) {
          setPendingId(pending);
          setActResult(
            `Denied (needs a person). Queued as ${pending}. Go to Approvals next.`,
          );
        } else {
          setActResult(`Denied: ${JSON.stringify(result.data)}`);
        }
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
      <HowToGuide highlight="1" />

      <section className="panel">
        <h2>Step 1 — Playground</h2>
        <p className="muted">
          Pick a scenario, then <strong>Run action</strong>. “Explain rules” only shows
          the checklist; it does not queue an approval.
        </p>

        <fieldset className="scenario-list">
          <legend>Scenario</legend>
          {SCENARIOS.map((item) => (
            <label key={item.id} className="scenario-option">
              <input
                type="radio"
                name="scenario"
                checked={scenarioId === item.id}
                onChange={() => pickScenario(item.id)}
              />
              <span>
                <strong>{item.label}</strong>
                <span className="muted"> — {item.blurb}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <p className="callout">
          Current: <strong>{scenario.label}</strong>
        </p>

        <div className="field-grid">
          <label>
            Agent
            <input
              value={form.agent_id}
              onChange={(e) => update("agent_id", e.target.value)}
            />
          </label>
          <label>
            Tool
            <input value={form.tool} onChange={(e) => update("tool", e.target.value)} />
          </label>
          <label>
            Model
            <input value={form.model} onChange={(e) => update("model", e.target.value)} />
          </label>
          <label>
            Caller
            <input value={form.caller} onChange={(e) => update("caller", e.target.value)} />
          </label>
          <label>
            Purpose
            <input
              value={form.purpose}
              onChange={(e) => update("purpose", e.target.value)}
            />
          </label>
          <label>
            Lawful basis
            <input
              value={form.lawful_basis ?? ""}
              onChange={(e) => update("lawful_basis", e.target.value)}
            />
          </label>
          <label>
            Environment
            <input
              value={form.environment ?? "dev"}
              onChange={(e) => update("environment", e.target.value)}
            />
          </label>
          <label>
            Data class
            <input
              value={form.data_class ?? "internal"}
              onChange={(e) => update("data_class", e.target.value)}
            />
          </label>
        </div>
        <label className="block-label">
          Prompt
          <textarea
            value={form.prompt}
            onChange={(e) => update("prompt", e.target.value)}
            aria-label="prompt"
          />
        </label>
        <div className="row" style={{ marginTop: "0.75rem" }}>
          <button type="button" onClick={() => void onAct()}>
            Run action
          </button>
          <button type="button" className="secondary" onClick={() => void onExplain()}>
            Explain rules only
          </button>
        </div>
        {error ? <p className="tag deny">{error}</p> : null}
        {actResult ? <p className="result-line">{actResult}</p> : null}
        {pendingId ? (
          <div className="next-step">
            <p>
              Next: open Approvals and click <strong>Approve + retry</strong> for queue id{" "}
              <span className="mono">{pendingId}</span>.
            </p>
            <Link className="button" href="/approvals">
              Step 2 — go to Approvals
            </Link>
          </div>
        ) : null}
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
          <p className="muted">Run an action or Explain to fill this list.</p>
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
