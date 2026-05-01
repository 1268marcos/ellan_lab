import { expect, test } from "@playwright/test";

const token = process.env.E2E_PUBLIC_AUTH_TOKEN?.trim();
const locker =
  process.env.E2E_CHECKOUT_LOCKER_ID?.trim() || "SP-CARAPICUIBA-JDMARILU-LK-002";
const sku = process.env.E2E_CHECKOUT_SKU_ID?.trim() || "cookie_especial";
const slot = process.env.E2E_CHECKOUT_SLOT?.trim() || "3";

test.describe("Checkout público (P3 fluxo DEV opcional)", () => {
  test("simular pagamento DEV e ir para meus pedidos", async ({ page, context }) => {
    test.skip(
      !token,
      "Defina E2E_PUBLIC_AUTH_TOKEN (JWT público). Utilizador precisa email verificado, perfil fiscal 100% (BR/PT) e role admin_operacao ou auditoria; stack pickup/gateway/runtime no ar.",
    );

    await context.addInitScript((t: string) => {
      window.localStorage.setItem("ellan_public_auth_token", t);
    }, token as string);

    const qs = new URLSearchParams({
      region: "SP",
      locker_id: locker,
      sku_id: sku,
      slot,
    });
    await page.goto(`/checkout?${qs.toString()}`);

    const devBtn = page.getByTestId("public-checkout-dev-simulate");
    await devBtn.waitFor({ state: "visible", timeout: 90_000 });

    page.once("dialog", (d) => d.accept());
    await devBtn.click();

    await expect(page).toHaveURL(/\/meus-pedidos\//, { timeout: 120_000 });
  });
});
