"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { HowToGuide } from "@/components/HowToGuide";
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
  const [success, setSuccess] = useState<string | null>(null);
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
    setSuccess(null);
    try {
      const result = await approveAction(item.id);
      setLastToken(result.approval_token);
      const retry = await agentAct({
        ...result.action,
        approval_token: result.approval_token,
      });
      if (!retry.ok) {
        setError(`Token issued but retry failed: ${JSON.stringify(retry.data)}`);
      } else {
        setSuccess(
          `Approved and retried successfully for ${item.action.tool}. Check Audit for the allow line.`,
        );
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
    setSuccess(null);
    try {
      await rejectAction(id);
      setSuccess("Rejected. The action stays denied.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <HowToGuide highlight="2" />

      <section className="panel">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>Step 2 — Approval queue</h2>
          <button type="button" className="secondary" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
        <p className="muted">
          After Playground denies a high-impact tool, the row appears here.{" "}
          <strong>Approve + retry</strong> mints a signed token and runs the action again.
          If this page errors about admin token, Vercel{" "}
          <span className="mono">NEXT_PUBLIC_ADMIN_TOKEN</span> must match Azure{" "}
          <span className="mono">gateway-admin-token</span> (often{" "}
          <span className="mono">dev-admin-token</span>), then redeploy.
        </p>
        {error ? <p className="tag deny">{error}</p> : null}
        {success ? <p className="tag allow">{success}</p> : null}
        {lastToken ? (
          <p className="muted">
            Last token (auto-used on retry): <span className="mono">{lastToken}</span>
          </p>
        ) : null}
        {success ? (
          <div className="next-step">
            <Link className="button" href="/audit">
              Step 3 — open Audit
            </Link>
          </div>
        ) : null}
      </section>

      <section className="panel">
        {items.length === 0 ? (
          <div>
            <p className="muted">
              No pending approvals yet. That usually means you have not run the “Needs
              approval” scenario, or this Container App replica restarted (the queue is
              in memory).
            </p>
            <Link className="button" href="/playground">
              Back to Playground
            </Link>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>What was blocked</th>
                <th>Caller</th>
                <th>Purpose</th>
                <th>Your decision</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="mono">{item.action.agent_id}</div>
                    <div>
                      <strong>{item.action.tool}</strong>
                    </div>
                    <div className="muted mono">{item.id.slice(0, 8)}…</div>
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
