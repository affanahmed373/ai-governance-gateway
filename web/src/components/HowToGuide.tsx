import Link from "next/link";

const STEPS = [
  {
    n: "1",
    title: "Deny it",
    body: "Open Playground, keep the default “delete invoice” scenario, click Run action. The gateway should deny and queue an approval.",
    href: "/playground",
    cta: "Playground",
  },
  {
    n: "2",
    title: "Approve it",
    body: "Open Approvals, click Refresh if needed, then Approve + retry. That mints a signed token and sends the action again.",
    href: "/approvals",
    cta: "Approvals",
  },
  {
    n: "3",
    title: "Check the trail",
    body: "Open Audit, click Load. You should see a deny, then an allow. Prompts are stored as hashes only.",
    href: "/audit",
    cta: "Audit",
  },
] as const;

export function HowToGuide({ highlight }: { highlight?: "1" | "2" | "3" }) {
  return (
    <section className="panel howto" aria-label="How to use this console">
      <h2>How to use this console (3 steps)</h2>
      <p className="muted">
        High-impact tools (like deleting an invoice) are blocked until a person approves.
        This UI is that person.
      </p>
      <ol className="howto-steps">
        {STEPS.map((step) => (
          <li
            key={step.n}
            className={highlight === step.n ? "howto-step is-current" : "howto-step"}
          >
            <span className="howto-num" aria-hidden>
              {step.n}
            </span>
            <div>
              <strong>{step.title}</strong>
              <p className="muted">{step.body}</p>
              <Link className="button secondary" href={step.href}>
                {step.cta}
              </Link>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
