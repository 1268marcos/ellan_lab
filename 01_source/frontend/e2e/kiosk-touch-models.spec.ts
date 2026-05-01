import { expect, test } from "@playwright/test";

/**
 * Sprint 1 — trilha **E** («E2E KIOSK assistido»): smoke `/ops/kiosk-touch-models` + encadeamentos do plano.
 * Sessão OPS: mock `/public/auth/me*` + token em `localStorage`. Extensão: **Modelo A** → `/comprar`;
 * **Modelo B** → `/checkout` (sem query mínima → `public-checkout-invalid`). `VITE_ENABLE_OPS_ROUTES` no `webServer`.
 */
test.describe("OPS KIOSK touch — modelos v1 (assistido)", () => {
  test.beforeEach(async ({ page, context }) => {
    await context.addInitScript(() => {
      window.localStorage.setItem("ellan_public_auth_token", "e2e-playwright-ops-kiosk-touch");
    });

    await page.route(
      (url) => url.pathname === "/public/auth/me/roles",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ roles: [{ role: "admin_operacao" }] }),
        });
      },
    );
    await page.route(
      (url) => url.pathname === "/public/auth/me",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            user: {
              id: "e2e-kiosk-touch",
              full_name: "E2E KIOSK touch",
              email: "e2e-kiosk-touch@ellan.local",
            },
          }),
        });
      },
    );
  });

  test("carrega cockpit, quatro modelos, checklist n≥8 e export JSON", async ({ page }) => {
    await page.goto("/ops/kiosk-touch-models");

    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible();
    await expect(page.getByRole("heading", { level: 1, name: /KIOSK touch — modelos de tela v1/i })).toBeVisible();

    await expect(page.getByRole("button", { name: /Modelo A — Quick Buy/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Modelo B — Guided Buy/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Modelo C — Pickup Fast Lane/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Modelo D — Partner Allocation/i })).toBeVisible();

    await page.getByRole("button", { name: /Modelo B — Guided Buy/i }).click();
    await expect(page.getByRole("heading", { level: 2, name: /Modelo B — Guided Buy/i })).toBeVisible();

    const firstCheck = page.getByRole("checkbox").first();
    await expect(firstCheck).toBeVisible();
    await firstCheck.check();
    const checklistSection = page.locator("section").filter({ has: page.locator("#kiosk-usability-n8-heading") });
    await expect(checklistSection).toContainText(/1\s*\/\s*8/);

    await page.getByRole("button", { name: /Recarregar definições/i }).click();
    await expect(page.getByRole("heading", { level: 2, name: /Modelo B — Guided Buy/i })).toBeVisible();

    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: /Exportar checklist \(JSON\)/i }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^SPRINT1_KIOSK_TOUCH_USABILITY_N8_/i);
  });

  test("Modelo A — CTA primário abre catálogo /comprar", async ({ page }) => {
    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: /Modelo A — Quick Buy/i }).click();
    await page.getByRole("link", { name: /Abrir catálogo \(fluxo compra\)/i }).click();

    await expect(page).toHaveURL(/\/comprar/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: /Escolha seu produto/i })).toBeVisible({ timeout: 30_000 });
  });

  test("Modelo B — CTA primário abre /checkout (laboratório; sem query → checkout inválido)", async ({ page }) => {
    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: /Modelo B — Guided Buy/i }).click();
    await page.getByRole("link", { name: /Abrir checkout \(laboratório\)/i }).click();

    await expect(page).toHaveURL(/\/checkout(?:\?|$)/, { timeout: 15_000 });
    await expect(page.getByTestId("public-checkout-invalid")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /Checkout inválido/i })).toBeVisible();
  });
});
