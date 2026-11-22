import { expect, test } from "@playwright/test";

test("home shows the gateway brand and approval path", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "AI Governance Gateway" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open approval queue" })).toBeVisible();
});
