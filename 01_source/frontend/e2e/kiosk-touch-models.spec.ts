import { expect, test, type Page } from "@playwright/test";

const E2E_PT_LOCKER = {
  locker_id: "e2e-kiosk-pt-1",
  display_name: "E2E Locker PT",
  active: true,
  payment_methods: ["MBWAY"],
  country_code: "PT",
  province_code: "PT-13",
};

function isLabHost(hostname: string) {
  return hostname === "127.0.0.1" || hostname === "localhost";
}

type InstallKioskPtMocksOptions = {
  /** Uma gaveta ativa + estado AVAILABLE no runtime (passo vitrine → secção 2). */
  withSelectableCatalog?: boolean;
  /** Mock `POST` order-pickup `/kiosk/orders` após formulário válido. */
  mockKioskOrderPost?: boolean;
  /** Mock `POST` gateway `/gateway/pagamento` (resposta APPROVED → chama payment-approved no cliente). */
  mockGatewayPagamentoPost?: boolean;
  /** Mock `POST` order-pickup `kiosk/orders/{id}/payment-approved` (após gateway APPROVED). */
  mockPaymentApprovedPost?: boolean;
  /** Mock `POST` order-pickup `/kiosk/identify` (secção 4 após pagamento). */
  mockKioskIdentifyPost?: boolean;
};

const E2E_CATALOG_SLOT = {
  slot: 1,
  sku_id: "sku-e2e-kiosk-pt",
  name: "Produto E2E KIOSK PT",
  is_active: true,
  amount_cents: 199,
  currency: "EUR",
};

const E2E_LOCKER_SLOT_ROW = { slot: 1, state: "AVAILABLE", product_id: "sku-e2e-kiosk-pt" };

const E2E_KIOSK_ORDER_RESPONSE = {
  order_id: "e2e-order-pt-1",
  allocation_id: "e2e-allocation-1",
  slot: 1,
  amount_cents: 199,
  payment_method: "MBWAY",
  payment_status: "PENDING",
  payment_instruction_type: "MBWAY_PUSH",
  ttl_sec: 600,
  status: "created",
};

/**
 * Mocks mínimos para `RegionPage` PT kiosk (gateway lockers, geo order-pickup, runtime slots)
 * sem depender de `backend_*` no lab — trilha **E** assistida.
 * Aceita `localhost` e `127.0.0.1` (Vite / env do browser).
 */
async function installKioskPtLabMocks(page: Page, options: InstallKioskPtMocksOptions = {}) {
  const {
    withSelectableCatalog = false,
    mockKioskOrderPost = false,
    mockGatewayPagamentoPost = false,
    mockPaymentApprovedPost = false,
    mockKioskIdentifyPost = false,
  } = options;

  await page.route(
    (url) =>
      isLabHost(url.hostname) &&
      url.port === "8003" &&
      url.pathname === "/dev-admin/base/lockers",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [E2E_PT_LOCKER] }),
      });
    },
  );

  await page.route(
    (url) =>
      isLabHost(url.hostname) &&
      url.port === "8000" &&
      url.pathname === "/lockers" &&
      url.searchParams.get("region") === "PT",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [E2E_PT_LOCKER] }),
      });
    },
  );

  await page.route(
    (url) =>
      isLabHost(url.hostname) &&
      url.port === "8200" &&
      url.pathname === "/catalog/slots",
    async (route) => {
      const body = withSelectableCatalog ? JSON.stringify([E2E_CATALOG_SLOT]) : "[]";
      await route.fulfill({ status: 200, contentType: "application/json", body });
    },
  );

  await page.route(
    (url) =>
      isLabHost(url.hostname) &&
      url.port === "8200" &&
      url.pathname === "/locker/slots",
    async (route) => {
      const body = withSelectableCatalog ? JSON.stringify([E2E_LOCKER_SLOT_ROW]) : "[]";
      await route.fulfill({ status: 200, contentType: "application/json", body });
    },
  );

  if (mockPaymentApprovedPost) {
    await page.route(
      (url) =>
        isLabHost(url.hostname) &&
        url.port === "8003" &&
        url.pathname.includes("/kiosk/orders/") &&
        url.pathname.endsWith("/payment-approved"),
      async (route) => {
        if (route.request().method() !== "POST") {
          await route.continue();
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            order_id: "e2e-order-pt-1",
            allocation_id: "e2e-allocation-1",
            slot: 1,
            status: "paid",
            payment_method: "MBWAY",
            message: "Pagamento confirmado (E2E).",
            receipt_code: "E2E-RC-PT-1",
            fiscal: { receipt_code: "E2E-RC-PT-1" },
          }),
        });
      },
    );
  }

  if (mockGatewayPagamentoPost) {
    await page.route(
      (url) =>
        isLabHost(url.hostname) && url.port === "8000" && url.pathname === "/gateway/pagamento",
      async (route) => {
        if (route.request().method() !== "POST") {
          await route.continue();
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            result: "approved",
            payment: {
              status: "APPROVED",
              gateway_status: "CAPTURED",
              metodo: "MBWAY",
              transaction_id: "e2e-tx-gateway-1",
            },
          }),
        });
      },
    );
  }

  if (mockKioskOrderPost) {
    await page.route(
      (url) => isLabHost(url.hostname) && url.port === "8003" && url.pathname === "/kiosk/orders",
      async (route) => {
        if (route.request().method() !== "POST") {
          await route.continue();
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(E2E_KIOSK_ORDER_RESPONSE),
        });
      },
    );
  }

  if (mockKioskIdentifyPost) {
    await page.route(
      (url) => isLabHost(url.hostname) && url.port === "8003" && url.pathname === "/kiosk/identify",
      async (route) => {
        if (route.request().method() !== "POST") {
          await route.continue();
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ok: true,
            order_id: "e2e-order-pt-1",
            phone: "+351910000001",
            email: "e2e-identify@ellan.local",
            message: "Identificação guardada (E2E).",
          }),
        });
      },
    );
  }
}

/**
 * Sprint 1 — trilha **E** («E2E KIOSK assistido»): smoke `/ops/kiosk-touch-models` + encadeamentos do plano.
 * Sessão OPS: mock `/public/auth/me*` + token em `localStorage`. **Modelo A** → `/comprar`;
 * **Modelo B** → `/checkout` (sem query mínima → `public-checkout-invalid`);
 * **Modelo C** → `/ops/pt/kiosk` (mocks: vitrine, orders, gateway, payment-approved, `/kiosk/identify`); **Modelo D** → `/ops/dev/slots`.
 * `VITE_ENABLE_OPS_ROUTES` no `webServer`.
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

  test("Modelo C — CTA primário abre simulador KIOSK OPS (PT)", async ({ page }) => {
    await installKioskPtLabMocks(page);

    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: /Modelo C — Pickup Fast Lane/i }).click();
    await page.getByRole("link", { name: /Abrir kiosk OPS \(PT\)/i }).click();

    await expect(page).toHaveURL(/\/ops\/pt\/kiosk/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: /Simulador KIOSK — PT/i })).toBeVisible({
      timeout: 30_000,
    });

    await expect(page.getByRole("heading", { level: 2, name: /0\. Seleção da unidade física/i })).toBeVisible({
      timeout: 30_000,
    });
    const lockerSelect = page.getByLabel(/Locker/i);
    await expect(lockerSelect).toBeVisible({ timeout: 15_000 });
    await expect(lockerSelect).toHaveValue("e2e-kiosk-pt-1");
  });

  test("Modelo C — KIOSK PT: vitrine, MB WAY e criar pedido (POST mock)", async ({ page }) => {
    await installKioskPtLabMocks(page, { withSelectableCatalog: true, mockKioskOrderPost: true });

    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: /Modelo C — Pickup Fast Lane/i }).click();
    await page.getByRole("link", { name: /Abrir kiosk OPS \(PT\)/i }).click();
    await expect(page).toHaveURL(/\/ops\/pt\/kiosk/, { timeout: 15_000 });

    await expect(page.getByRole("button", { name: /Gaveta 1/i })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: /Gaveta 1/i }).click();

    await expect(page.getByRole("heading", { name: /2\. Criar pedido KIOSK/i })).not.toContainText(/Selecione um produto primeiro/i);

    await page.getByLabel(/Telefone MB WAY/i).fill("+351912345678");
    await page.getByRole("button", { name: /^Criar pedido KIOSK$/i }).click();

    await expect(page.getByText(/Pedido criado com sucesso/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/e2e-order-pt-1/).first()).toBeVisible();
  });

  test("Modelo C — KIOSK PT: pedido, pagamento (APPROVED) e identificação (mocks)", async ({ page }) => {
    await installKioskPtLabMocks(page, {
      withSelectableCatalog: true,
      mockKioskOrderPost: true,
      mockGatewayPagamentoPost: true,
      mockPaymentApprovedPost: true,
      mockKioskIdentifyPost: true,
    });

    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: /Modelo C — Pickup Fast Lane/i }).click();
    await page.getByRole("link", { name: /Abrir kiosk OPS \(PT\)/i }).click();
    await expect(page).toHaveURL(/\/ops\/pt\/kiosk/, { timeout: 15_000 });

    await page.getByRole("button", { name: /Gaveta 1/i }).click();
    await page.getByLabel(/Telefone MB WAY/i).fill("+351912345678");
    await page.getByRole("button", { name: /^Criar pedido KIOSK$/i }).click();
    await expect(page.getByText(/Pedido criado com sucesso/i)).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: /Iniciar pagamento no gateway/i }).click();

    await expect(page.getByText(/Resposta do gateway/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/comprovante:\s*E2E-RC-PT-1/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Comprovante fiscal")).toBeVisible();

    await page.getByPlaceholder("+5511999999999 / +351912345678").fill("+351910000001");
    await page.getByPlaceholder("cliente@email.com").fill("e2e-identify@ellan.local");
    await page.getByRole("button", { name: /Salvar identificação/i }).click();

    await expect(page.getByText(/Identificação salva/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.locator("pre").filter({ hasText: "e2e-identify@ellan.local" })).toBeVisible();
  });

  test("Modelo D — CTA primário abre alocação por slot (dev)", async ({ page }) => {
    await page.goto("/ops/kiosk-touch-models");
    await expect(page.getByTestId("ops-kiosk-touch-models-page")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: /Modelo D — Partner Allocation/i }).click();
    await page.getByRole("link", { name: /Abrir alocação por slot \(dev\)/i }).click();

    await expect(page).toHaveURL(/\/ops\/dev\/slots/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: /Ops — Alocação de Produtos por Slot/i })).toBeVisible({
      timeout: 30_000,
    });
  });
});
