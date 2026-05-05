
import { expect, test } from "@playwright/test";

/**
 * Sprint 1 — extensão do E2E assistido (registo 2026-05-01): primeiro passo da jornada **pública**
 * antes do checkout (`/comprar` → `PublicCatalogPage`). Não depende de stack gateway/runtime no ar para
 * o hero (título e filtros renderizam de imediato).
 */
test.describe("Jornada pública — catálogo (/comprar)", () => {
  test("mostra hero «Escolha seu produto» e filtros de catálogo", async ({ page }) => {
    await page.goto("/comprar");
    await expect(page.getByRole("heading", { level: 1, name: /Escolha seu produto/i })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("group", { name: /Filtros de catálogo/i })).toBeVisible();
  });
});

