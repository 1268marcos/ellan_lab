# Sprint 1 — FE / KIOSK v1 (registo Lab, 2026-04-30)

Espelho do painel e percentuais: **`docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`** — secção **Sprint 1**, **Mapa de trilhas**, **Metodo** *(x)* e snapshot «trilhas C / D / E / F1 / F2».

## Leitura de painel (**Metodo** *(x)*)

| Item checklist (Sprint 1) | Indicador |
| --- | ---: |
| Migração de estilos (F1+F2 agregados) | **~25%** |
| Store + boundaries | **100%** |
| TS incremental | **~93%** |
| Protótipos KIOSK | **~66%** |
| E2E assistido | **~18%** |
| **Média dos 6 itens** | **~67%** |

## Evidências no repositório (`01_source/frontend`)

- **F2 — CSS kiosk/OPS:** `src/styles/opsKioskTouchModelsChrome.css` + `src/pages/OpsKioskTouchModelsPage.tsx`.
- **F1 — checkout público:** `src/styles/publicCheckoutChrome.css` (fatias 1–4 + media queries mobile ≤640/480px).
- **D — cockpit KIOSK:** refinamentos mobile, `focus-visible`, `prefers-reduced-motion`, atributos `aria-*` (commits trilha D).
- **E — E2E assistido:** `e2e/kiosk-touch-models.spec.ts` (modelos **A–D**: `/comprar`, `/checkout`, `/ops/pt/kiosk`, `/ops/dev/slots` + export JSON checklist n≥8); `e2e/public-catalog-to-checkout.spec.ts` (POST sucesso + 409).
- **C — TS incremental:** `src/components/OpsScenarioPresets.tsx`, `OpsHelpTutorialModal.tsx` em `tsconfig.strict-core.json` (com `OpsRouteHelpButton`).

## Verificação local típica

```bash
cd 01_source/frontend
npm run typecheck && npm run typecheck:strict-core && npm run build
npx playwright test e2e/kiosk-touch-models.spec.ts
```

## Nota sobre `Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt`

O `.gitignore` do repo não versiona `.txt` em `docs/`; pode manter-se um espelho manual desse ficheiro para o eixo Fiscal/Invoices. Este `.md` é o **registo Sprint 1** anexável ao daily ou ao pacote de governança no git.
