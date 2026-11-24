import type { AgentActionBody } from "@/lib/gateway";

export type Scenario = {
  id: string;
  label: string;
  blurb: string;
  body: AgentActionBody;
};

/** Ready-made playground bodies so you do not have to invent fields. */
export const SCENARIOS: Scenario[] = [
  {
    id: "needs-approval",
    label: "Needs approval (delete invoice)",
    blurb: "High-impact tool. Expect deny + a row in Approvals.",
    body: {
      agent_id: "spice-invoice-agent",
      tool: "delete_invoice",
      model: "gpt-4o-mini-eu",
      prompt: "Delete supplier invoice INV-42 after the PG Tips price check.",
      purpose: "supplier_price_check",
      lawful_basis: "contract",
      environment: "prod",
      data_class: "internal",
      caller: "team-a",
    },
  },
  {
    id: "allowed-read",
    label: "Allowed (compare prices)",
    blurb: "Normal tool. Expect allow without Approvals.",
    body: {
      agent_id: "spice-invoice-agent",
      tool: "compare_prices",
      model: "gpt-4o-mini-eu",
      prompt: "Which supplier is cheaper for PG Tips this month?",
      purpose: "supplier_price_check",
      lawful_basis: "contract",
      environment: "prod",
      data_class: "internal",
      caller: "team-a",
    },
  },
  {
    id: "peer-denied",
    label: "Denied peer (catalog → spice)",
    blurb: "Wrong peer agent. Expect target_agent_not_allowed (no Approvals row).",
    body: {
      agent_id: "cloth-catalog-agent",
      tool: "draft_caption",
      model: "gpt-4o-mini-eu",
      prompt: "Draft an Instagram caption for the winter coats drop.",
      purpose: "catalog_post",
      environment: "dev",
      data_class: "public",
      caller: "shop-staff",
      target_agent: "spice-invoice-agent",
    },
  },
];
