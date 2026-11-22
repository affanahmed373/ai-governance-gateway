"use client";

import { useCallback, useEffect, useState } from "react";

import {
  type PendingApproval,
  agentAct,
  approveAction,
  listApprovals,
  rejectAction,
} from "@/lib/gateway";

export default function ApprovalsPage() {
  const [items, setItems] = useState<PendingApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastToken, setLastToken] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      setItems(await listApprovals());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onApprove(item: PendingApproval) {
    setBusy(item.id);
    setError(null);
    try {
      const result = await approveAction(item.id);
      setLastToken(result.approval_token);
      const retry = await agentAct({
        ...result.action,
        approval_token: result.approval_token,
      });
      if (!retry.ok) {
        setError(`Token issued but retry failed: ${JSON.stringify(retry.data)}`);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  async function onReject(id: string) {
    setBusy(id);
    setError(null);
    try {
      await rejectAction(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <section className="panel">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>Approval queue</h2>
          <button type="button" className="secondary" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
        <p className="muted">
          Items appear when <span className="mono">POST /v1/agent/act</span> is denied
          with <span className="mono">human_approval_required</span>.
        </p>
        {error ? <p className="tag deny">{error}</p> : null}
        {lastToken ? (
          <p>
            Last token (also used for an automatic retry):{" "}
            <span className="mono">{lastToken}</span>
          </p>
        ) : null}
      </section>

      <section className="panel">
        {items.length === 0 ? (
          <p className="muted">No pending approvals. Seed one from the playground.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Agent / tool</th>
                <th>Caller</th>
                <th>Purpose</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="mono">{item.action.agent_id}</div>
                    <div>{item.action.tool}</div>
                  </td>
                  <td className="mono">{item.action.caller}</td>
                  <td>{item.action.purpose}</td>
                  <td>
                    <div className="row">
                      <button
                        type="button"
                        disabled={busy === item.id}
                        onClick={() => void onApprove(item)}
                      >
                        Approve + retry
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={busy === item.id}
                        onClick={() => void onReject(item.id)}
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
