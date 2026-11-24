import { describe, expect, it } from "vitest";

import { SCENARIOS } from "./scenarios";

describe("SCENARIOS", () => {
  it("includes a high-impact delete that needs approval", () => {
    const needs = SCENARIOS.find((s) => s.id === "needs-approval");
    expect(needs?.body.tool).toBe("delete_invoice");
  });

  it("includes an allowed compare_prices path", () => {
    const allowed = SCENARIOS.find((s) => s.id === "allowed-read");
    expect(allowed?.body.tool).toBe("compare_prices");
  });
});
