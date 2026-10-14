import { expect, test } from "@playwright/test";

import { expectNoSeriousA11yIssues } from "./a11y";

test("landing page explains the product and links to the sample plan", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { level: 1, name: /Plan your degree around your job/ }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "How it works" })).toBeVisible();
  await expect(page.getByText("We never ask for your school password.")).toBeVisible();
  await expect(page.getByText(/confirm your plan with your academic advisor/i)).toBeVisible();
  await expectNoSeriousA11yIssues(page);

  await page.getByRole("main").getByRole("link", { name: "See a sample plan" }).click();
  await expect(page).toHaveURL(/\/demo$/);
});

test("pages never scroll sideways on a phone", async ({ page }) => {
  for (const path of ["/", "/demo"]) {
    await page.goto(path);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, `${path} scrolls sideways`).toBeLessThanOrEqual(0);
  }
});

test("dark mode is readable and accessible", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  for (const path of ["/", "/demo"]) {
    await page.goto(path);
    await expectNoSeriousA11yIssues(page);
  }
});

test("the style guide is not served in production", async ({ request }) => {
  const response = await request.get("/styleguide");
  expect(response.status()).toBe(404);
});
