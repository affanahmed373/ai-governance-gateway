import { describe, expect, it } from "vitest";

import { formatDecision } from "./format";

describe("formatDecision", () => {
  it("labels an allow", () => {
    expect(formatDecision("allowed")).toBe("allowed");
  });

  it("strips denied prefix for display", () => {
    expect(formatDecision("denied:human_approval_required")).toBe(
      "human_approval_required",
    );
  });
});
