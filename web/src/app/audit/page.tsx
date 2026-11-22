"use client";

import { useState } from "react";

import { type AuditRecord, listAudit, listModels } from "@/lib/gateway";
import { formatDecision } from "@/lib/format";

export default function AuditPage() {
  const [items, setItems] = useState<AuditRecord[]>([]);
  const [models, setModels] = useState<
    Array<{ id: string; provider?: string; region?: string; status?: string }>
  >([]);
  const [caller, setCaller] = useState("");
  const [agentId, setAgentId] = useState("");
  const [rule, setRule] = useState("");
  const [decision, setDecision] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [audit, modelList] = await Promise.all([
        listAudit({
          caller: caller || undefined,
          agent_id: agentId || undefined,
          rule: rule || undefined,
          decision: decision || undefined,
        }),
        listModels(),
      ]);
      setItems(audit);
      setModels(modelList);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <>
      <section className="panel">
        <h2>Audit log</h2>
        <p className="muted">
          Recent decisions from this gateway process (in-memory ring). Durable logs still
          go to stdout / Log Analytics. Prompts are hashes only.
        </p>
        <div className="row">
          <input
            placeholder="caller"
            value={caller}
            onChange={(e) => setCaller(e.target.value)}
          />
          <input
            placeholder="agent_id"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
          />
          <input placeholder="rule" value={rule} onChange={(e) => setRule(e.target.value)} />
          <input
            placeholder="decision prefix (allowed / denied)"
            value={decision}
            onChange={(e) => setDecision(e.target.value)}
          />
          <button type="button" onClick={() => void load()}>
            Load
          </button>
        </div>
        {error ? <p className="tag deny">{error}</p> : null}
      </section>

      <section className="panel">
        <h2>Records</h2>
        {items.length === 0 ? (
          <p className="muted">No rows yet. Load after running the playground.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Decision</th>
                <th>Caller</th>
                <th>Agent</th>
                <th>Rule</th>
                <th>Prompt hash</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const label = formatDecision(item.decision);
                const allowed = item.decision === "allowed";
                return (
                  <tr key={item.request_id}>
                    <td>
                      <span className={`tag ${allowed ? "allow" : "deny"}`}>{label}</span>
                    </td>
                    <td className="mono">{item.caller}</td>
                    <td className="mono">{item.agent_id ?? "—"}</td>
                    <td className="mono">{item.rule ?? "—"}</td>
                    <td className="mono">{item.prompt_sha256?.slice(0, 12)}…</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h2>Approved models</h2>
        {models.length === 0 ? (
          <p className="muted">Load to fetch the registry.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Id</th>
                <th>Provider</th>
                <th>Region</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <td className="mono">{model.id}</td>
                  <td>{model.provider}</td>
                  <td>{model.region}</td>
                  <td>{model.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
