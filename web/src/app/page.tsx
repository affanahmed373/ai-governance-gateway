import Link from "next/link";

import { gatewayUrl } from "@/lib/gateway";

export default function HomePage() {
  return (
    <>
      <section className="panel">
        <h2>What this console is for</h2>
        <p>
          Reviewers approve high-impact agent actions. The gateway no longer trusts a
          checkbox named <span className="mono">human_approved</span>. Approving here
          mints a signed <span className="mono">approval_token</span>; the retry must
          carry that token.
        </p>
        <p className="muted">
          API base: <span className="mono">{gatewayUrl()}</span>
        </p>
        <div className="row" style={{ marginTop: "1rem" }}>
          <Link className="button" href="/approvals">
            Open approval queue
          </Link>
          <Link className="button secondary" href="/playground">
            Try the playground
          </Link>
        </div>
      </section>
      <section className="panel">
        <h2>Typical path</h2>
        <ol>
          <li>Playground (or an agent) calls a high-impact tool and gets HTTP 403.</li>
          <li>The deny creates a pending item in Approvals.</li>
          <li>You approve; copy or retry with the issued token.</li>
          <li>Audit shows the deny and the later allow (prompt stored as a hash only).</li>
        </ol>
      </section>
    </>
  );
}
