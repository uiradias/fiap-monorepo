import { test, expect } from "@playwright/test";
import path from "node:path";
import { randomUUID } from "node:crypto";

const FIXTURE = path.resolve(
  __dirname, "..", "..", "smart-service", "tests", "fixtures", "sample-architecture.png");

test("register → upload → REPORT_READY", async ({ page }) => {
  const email = `e2e-${randomUUID().slice(0, 8)}@fiap.local`;
  const password = "hunter22-e2e";

  // Register
  await page.goto("/register");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/^password/i).fill(password);
  await page.getByLabel(/display name/i).fill("E2E Bot");
  await page.getByRole("button", { name: /register/i }).click();

  // Auto-login lands us on /upload
  await expect(page).toHaveURL(/\/upload$/, { timeout: 15_000 });

  // Pick the fixture file via the visible file input.
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(FIXTURE);
  await expect(page.getByText(/sample-architecture\.png/)).toBeVisible({ timeout: 15_000 });

  // Finalize
  await page.getByRole("button", { name: /finalize/i }).click();
  await expect(page).toHaveURL(/\/sessions\/[0-9a-f-]+$/, { timeout: 15_000 });

  // Wait for REPORT_READY in the timeline (smart-service is in e2e profile → fast path).
  await expect(page.getByText(/REPORT_READY/)).toBeVisible({ timeout: 90_000 });

  // Report block should render with the (fake) summary.
  await expect(page.getByText(/\(fake\) Architecture review of 1 asset\(s\)/)).toBeVisible();
});
