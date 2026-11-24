import { expect, test } from "@playwright/test";

test("home shows the guided three-step path", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "AI Governance Gateway" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "How to use this console (3 steps)" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Step 1 — open Playground" })).toBeVisible();
});

test("playground offers the needs-approval scenario", async ({ page }) => {
  await page.goto("/playground");
  await expect(
    page.getByRole("radio", { name: /Needs approval \(delete invoice\)/ }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Run action" })).toBeVisible();
});
