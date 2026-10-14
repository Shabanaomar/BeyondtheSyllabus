import { defineConfig, devices } from "@playwright/test";

const port = 3100;

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${port}`,
    trace: "retain-on-failure",
  },
  // Every flow is tested on real phone profiles (touch, mobile viewport and user agent) and on
  // desktop. iPhone 13 Mini is 375px wide and runs on WebKit, the engine behind iPhone Safari.
  projects: [
    { name: "iphone", use: { ...devices["iPhone 13 Mini"] } },
    { name: "android", use: { ...devices["Galaxy S24"] } },
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: {
    command: `npm run build && npm run start -- --port ${port}`,
    url: `http://localhost:${port}`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
