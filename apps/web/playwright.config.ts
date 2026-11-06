import { defineConfig, devices } from "@playwright/test";

// T10 (PRD §9.2): recorrido de demo contra API + web reales ya levantadas.
// E2E_BASE_URL por defecto http://localhost:3000; la API debe responder en NEXT_PUBLIC_API_URL.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    viewport: { width: 1440, height: 900 },
    locale: "es-ES",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
