import { expect, test } from "@playwright/test";

test.describe("Checkout público (P3 smoke)", () => {
  test("sem query params mostra checkout inválido", async ({ page }) => {
    await page.goto("/checkout");
    await expect(page.getByTestId("public-checkout-invalid")).toBeVisible();
    await expect(page.getByRole("heading", { name: /checkout inválido/i })).toBeVisible();
  });
});
