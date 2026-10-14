import { expect, test } from "@playwright/test";

import { expectNoSeriousA11yIssues } from "./a11y";

test("sample plan shows every dashboard card and says it is a sample", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByRole("note")).toContainText("made-up student");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Hi Maya, here's your spring");
  await expect(page.getByRole("img", { name: "62 of 120 units done" })).toBeVisible();
  await expect(page.getByText("On track to graduate in Spring 2028")).toBeVisible();

  const week = page.getByRole("region", { name: "Your week in Spring 2027" });
  await expect(week.getByRole("list", { name: "Mon schedule" })).toContainText("1:00–5:00 Work");

  const nextTerm = page.getByRole("region", { name: "Take these next term" });
  await expect(nextTerm.getByRole("heading", { level: 3 })).toHaveCount(3);
  await expect(nextTerm).toContainText("10 units");
  await expect(nextTerm).toContainText("you need it before ME 120");

  await expect(page.getByRole("region", { name: "Clubs you might like" })).toContainText(
    "American Society of Mechanical Engineers",
  );
  await expect(page.getByRole("region", { name: "Coming up for your career" })).toContainText(
    "Wednesday, February 24",
  );
  await expect(page.getByRole("link", { name: "Add everything to my calendar" })).toHaveAttribute(
    "href",
    "/demo/calendar.ics",
  );
  await expectNoSeriousA11yIssues(page);
});

test("sample calendar file imports cleanly", async ({ request }) => {
  const response = await request.get("/demo/calendar.ics");
  expect(response.ok()).toBe(true);
  expect(response.headers()["content-type"]).toContain("text/calendar");
  const body = await response.text();

  expect(body.startsWith("BEGIN:VCALENDAR\r\n")).toBe(true);
  expect(body.trimEnd().endsWith("END:VCALENDAR")).toBe(true);
  // Every line is CRLF-terminated and at most 75 octets.
  const lines = body.split("\r\n").filter(Boolean);
  for (const line of lines) {
    expect(new TextEncoder().encode(line).length).toBeLessThanOrEqual(75);
  }
  // Long lines are folded (CRLF + space); unfold before checking content.
  const text = body.replace(/\r\n /g, "");
  expect(text.match(/BEGIN:VEVENT/g)).toHaveLength(7);
  // Monday/Wednesday class: starts on the first Wednesday of instruction, skips Presidents' Day,
  // spring break and Farmworkers Day, and stops after the last day of instruction.
  expect(text).toContain("DTSTART;TZID=America/Los_Angeles:20270120T090000");
  expect(text).toContain("RRULE:FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20270513T075959Z");
  expect(text).toContain(
    "EXDATE;TZID=America/Los_Angeles:20270215T090000,20270322T090000,20270324T090000,20270331T090000",
  );
  expect(text).toContain("SUMMARY:Spring break (no classes)");
  expect(text).toContain("DTEND;VALUE=DATE:20270327");
});
