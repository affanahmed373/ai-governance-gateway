import Link from "next/link";

import { HowToGuide } from "@/components/HowToGuide";
import { gatewayUrl } from "@/lib/gateway";

export default function HomePage() {
  return (
    <>
      <section className="panel">
        <h2>Start here</h2>
        <p>
          This console is the human in the loop for the AI Governance Gateway. Agents
          can compare spice prices freely. Deleting an invoice (or publishing a catalog
          post) waits for you.
        </p>
        <p className="muted">
          Talking to API: <span className="mono">{gatewayUrl()}</span>
        </p>
        <div className="row" style={{ marginTop: "1rem" }}>
          <Link className="button" href="/playground">
            Step 1 — open Playground
          </Link>
          <Link className="button secondary" href="/approvals">
            Step 2 — Approvals
          </Link>
        </div>
      </section>
      <HowToGuide />
    </>
  );
}
