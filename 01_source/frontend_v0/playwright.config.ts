
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.FRONTEND_BASE_URL || "http://127.0.0.1:5173";

/** Sobe o Vite automaticamente (CI ou PLAYWRIGHT_START_VITE=1). Em lab, pode reutilizar `npm run dev` já no ar. */
const startVite = process.env.CI === "true" || process.env.PLAYWRIGHT_START_VITE === "1";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    ...devices["Desktop Chrome"],
    baseURL,
    trace: "on-first-retry",
  },
  webServer: startVite
    ? {
        command: "npm run dev -- --host 127.0.0.1 --port 5173",
        url: baseURL,
        reuseExistingServer: process.env.CI !== "true",
        timeout: 120_000,
        env: {
          ...process.env,
          VITE_DEV_BYPASS_AUTH: process.env.VITE_DEV_BYPASS_AUTH || "true",
          VITE_ENABLE_OPS_ROUTES: process.env.VITE_ENABLE_OPS_ROUTES || "true",
          VITE_ORDER_PICKUP_BASE_URL: process.env.VITE_ORDER_PICKUP_BASE_URL || "http://127.0.0.1:8003",
          VITE_GATEWAY_BASE_URL: process.env.VITE_GATEWAY_BASE_URL || "http://127.0.0.1:8000",
          VITE_RUNTIME_BASE_URL: process.env.VITE_RUNTIME_BASE_URL || "http://127.0.0.1:8200",
        },
      }
    : undefined,
});

