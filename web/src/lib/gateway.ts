/**
 * Thin client for the FastAPI gateway.
 * Types come from openapi-typescript (`npm run gen:api` in web/).
 */

const gatewayUrl = () =>
  (process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

const adminToken = () => process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? "dev-admin-token";

export type AgentActionBody = {
  agent_id: string;
  tool: string;
  model: string;
  prompt: string;
  purpose: string;
  lawful_basis?: string | null;
  environment?: string;
  data_class?: string;
  caller: string;
  approval_token?: string | null;
  step?: number;
  target_agent?: string | null;
};

export type PendingApproval = {
  id: string;
  status: string;
  created_at: number;
  action: AgentActionBody;
};

export type AuditRecord = {
  request_id: string;
  caller: string;
  model: string;
  decision: string;
  rule?: string;
  agent_id?: string;
  tool?: string;
  purpose?: string;
  prompt_sha256?: string;
};

export type ExplainCheck = {
  rule: string;
  passed: boolean;
  detail: string;
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (body.detail?.detail) return String(body.detail.detail);
    return JSON.stringify(body.detail ?? body);
  } catch {
    return response.statusText;
  }
}

export async function agentAct(body: AgentActionBody): Promise<{
  ok: boolean;
  status: number;
  data: Record<string, unknown>;
}> {
  const response = await fetch(`${gatewayUrl()}/v1/agent/act`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  return { ok: response.ok, status: response.status, data };
}

export function pendingApprovalIdFromDeny(data: Record<string, unknown>): string | null {
  const detail = data.detail;
  if (detail && typeof detail === "object" && "pending_approval_id" in detail) {
    return String((detail as { pending_approval_id: string }).pending_approval_id);
  }
  return null;
}

export async function listApprovals(): Promise<PendingApproval[]> {
  const response = await fetch(`${gatewayUrl()}/v1/admin/approvals`, {
    headers: { "X-Admin-Token": adminToken() },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await parseError(response));
  const body = (await response.json()) as { items: PendingApproval[] };
  return body.items;
}

export async function approveAction(
  id: string,
  reviewer = "console-reviewer",
): Promise<{ approval_token: string; action: AgentActionBody }> {
  const response = await fetch(`${gatewayUrl()}/v1/admin/approvals/${id}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": adminToken(),
    },
    body: JSON.stringify({ reviewer }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function rejectAction(id: string, reviewer = "console-reviewer"): Promise<void> {
  const response = await fetch(`${gatewayUrl()}/v1/admin/approvals/${id}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": adminToken(),
    },
    body: JSON.stringify({ reviewer }),
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function listAudit(params: {
  caller?: string;
  agent_id?: string;
  rule?: string;
  decision?: string;
}): Promise<AuditRecord[]> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) query.set(key, value);
  }
  const response = await fetch(`${gatewayUrl()}/v1/admin/audit?${query}`, {
    headers: { "X-Admin-Token": adminToken() },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await parseError(response));
  const body = (await response.json()) as { items: AuditRecord[] };
  return body.items;
}

export async function listModels(): Promise<
  Array<{
    id: string;
    provider?: string;
    region?: string;
    status?: string;
    max_data_class?: string;
  }>
> {
  const response = await fetch(`${gatewayUrl()}/v1/admin/models`, {
    headers: { "X-Admin-Token": adminToken() },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await parseError(response));
  const body = (await response.json()) as { items: Array<Record<string, string>> };
  return body.items as Array<{
    id: string;
    provider?: string;
    region?: string;
    status?: string;
    max_data_class?: string;
  }>;
}

export async function explainAction(body: AgentActionBody): Promise<{
  decision: string;
  checks: ExplainCheck[];
}> {
  const response = await fetch(`${gatewayUrl()}/v1/admin/explain`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": adminToken(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export { gatewayUrl };
