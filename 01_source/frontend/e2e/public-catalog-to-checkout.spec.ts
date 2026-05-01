import { expect, test } from "@playwright/test";

const GATEWAY_BASE = process.env.VITE_GATEWAY_BASE_URL || "http://127.0.0.1:8000";
const RUNTIME_BASE = process.env.VITE_RUNTIME_BASE_URL || "http://127.0.0.1:8200";
const LOCKER_ID = "SP-CARAPICUIBA-JDMARILU-LK-002";
const SKU_ID = "cookie_especial";
const SLOT = 3;

/** `localhost` vs `127.0.0.1` são origins distintos; Vite reutilizado pode usar o default do código. */
function matchesServiceBase(url: URL, baseStr: string): boolean {
  const base = new URL(baseStr);
  if (url.protocol !== base.protocol) return false;
  const loopback = (h: string) => h === "localhost" || h === "127.0.0.1";
  const sameHost =
    url.hostname === base.hostname ||
    (loopback(url.hostname) && loopback(base.hostname));
  const defaultPort = url.protocol === "https:" ? "443" : "80";
  const urlPort = url.port || defaultPort;
  const basePort = base.port || defaultPort;
  return sameHost && urlPort === basePort;
}

/**
 * Sprint 1 — encadear catálogo (`/comprar`) → `/checkout` com query mínima (plano 2026-05-01).
 * Mocka gateway + runtime para não depender da stack local; auth pickup para evitar redirect imediato a `/login`.
 */
async function installPickupAuthMocks(page: import("@playwright/test").Page) {
  await page.route(
    (url) => url.pathname === "/public/auth/me/roles",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ roles: [] }),
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
            id: "e2e-catalog-checkout",
            full_name: "E2E Catálogo→Checkout",
            email: "e2e-catalog-checkout@ellan.local",
            email_verified: true,
            fiscal_profile_completeness: 100,
          },
        }),
      });
    },
  );
}

async function installGatewayRuntimeMocks(page: import("@playwright/test").Page) {
  await page.route(
    (url) => matchesServiceBase(url, GATEWAY_BASE) && url.pathname === "/lockers",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              locker_id: LOCKER_ID,
              display_name: "Locker E2E",
              region: "SP",
              active: true,
              payment_methods: ["PIX"],
            },
          ],
        }),
      });
    },
  );

  await page.route(
    (url) => matchesServiceBase(url, RUNTIME_BASE) && url.pathname === "/catalog/slots",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            slot: SLOT,
            sku_id: SKU_ID,
            name: "Cookie laboratório",
            amount_cents: 499,
            currency: "BRL",
            is_active: true,
            locker_id: LOCKER_ID,
            updated_at: new Date().toISOString(),
          },
        ]),
      });
    },
  );

  await page.route(
    (url) => matchesServiceBase(url, RUNTIME_BASE) && url.pathname === "/locker/slots",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            slot: SLOT,
            state: "AVAILABLE",
            product_id: null,
            updated_at: new Date().toISOString(),
          },
        ]),
      });
    },
  );

  await page.route(
    (url) =>
      matchesServiceBase(url, RUNTIME_BASE) &&
      url.pathname === `/catalog/skus/${encodeURIComponent(SKU_ID)}`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          sku_id: SKU_ID,
          name: "Cookie laboratório",
          amount_cents: 499,
          currency: "BRL",
        }),
      });
    },
  );
}

test.describe("Jornada pública — catálogo → checkout (query mínima)", () => {
  test.beforeEach(async ({ page, context }) => {
    await context.addInitScript(() => {
      window.localStorage.setItem("ellan_public_auth_token", "e2e-playwright-catalog-checkout");
    });
    await installPickupAuthMocks(page);
    await installGatewayRuntimeMocks(page);
  });

  test("Comprar agora navega para checkout com resumo do pedido", async ({ page }) => {
    await page.goto(`/comprar?region=SP&locker_id=${encodeURIComponent(LOCKER_ID)}`);

    await expect(page.getByRole("heading", { level: 1, name: /Escolha seu produto/i })).toBeVisible({ timeout: 30_000 });

    // O nome acessível vem do aria-label ("Reservar … - Gaveta N"), não do texto "Comprar agora".
    const buy = page.getByRole("button", {
      name: new RegExp(`Reservar .+ - Gaveta ${SLOT}`, "i"),
    });
    await expect(buy).toBeEnabled({ timeout: 30_000 });
    await buy.click();

    await expect(page).toHaveURL(/\/checkout\?/, { timeout: 15_000 });
    await expect(page).toHaveURL(new RegExp(`locker_id=${LOCKER_ID.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    await expect(page).toHaveURL(/sku_id=cookie_especial/);
    await expect(page).toHaveURL(/slot=3(?:&|$)/);

    await expect(page.getByRole("heading", { name: /Resumo do Pedido/i })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Produto selecionado/i)).toBeVisible();
    await expect(page.getByText(/Cookie laboratório/i).first()).toBeVisible();
  });
});
