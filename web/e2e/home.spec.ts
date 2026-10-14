import { expect, test } from "@playwright/test";

import { expectNoSeriousA11yIssues } from "./a11y";

test("home page renders and is accessible", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Beyond the Syllabus" })).toBeVisible();
  await expect(page.getByText(/confirm your plan with your academic advisor/i)).toBeVisible();
  await expectNoSeriousA11yIssues(page);
});
