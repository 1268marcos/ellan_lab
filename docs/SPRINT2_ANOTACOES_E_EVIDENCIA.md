# Sprint 2 — anotações e evidência no lab

Documento vivo para **acompanhar a Sprint 2** (Fiscal + Contábil, dias 10–18 do plano 30 dias) e apontar **onde está a evidência no repositório**. Alinhar com `docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md` (secção **Sprint 2**, **gate v2**, **D10–D18**).

**Carimbo da última atualização deste ficheiro:** 2026-04-30 (sessão: pytest list `status`/datas + compare por `current_id`/`previous_id`; sessões anteriores: `owner` LIKE, `keep_minimum`, P0-1b, gate v2, D18).

---

## Resumo executivo (evidência automática)

| Área | Comando | Resultado esperado (lab) |
| ---- | ------- | ------------------------- |
| **Frontend** | `cd 01_source/frontend && npm test -- --run` | Vitest **49** testes em ficheiros `*.test.js` do projeto (incl. utilitários fiscais / Sprint 2 na tabela *Cobertura de testes* abaixo). |
| **Backend fiscal D15–D17** | `cd 01_source/backend/billing_fiscal_service && PYTHONPATH=. .venv/bin/pytest tests/test_accounting_approvals_*.py -q` | **18** testes: listagem (`owner`, `status`, datas), compare (últimos dois / ids explícitos), post/latest, retention/divergence, helpers diff D17. |

Estes números mudam quando acrescentares testes; após cada entrega relevante, atualizar esta tabela e a **Registo de incrementos**.

---

## Objetivo em uma frase

Fechar **P0 fiscal/contábil** com artefactos anexáveis ao daily ou ao ZIP (`fiscal/management-daily`, `fiscal/accounting-close`), até o **gate v2**: Fiscal ≥50%, Contábil ≥40%, consolidado Sprint 2 ≥55%, **e** nota P0 ≥24 caracteres no cockpit do gate (ver util abaixo).

---

## Gate v2 (comité 2026-05-01)

| Métrica            | Limiar |
| ------------------ | -----: |
| Fiscal             |   ≥50% |
| Contábil           |   ≥40% |
| Consolidado S2     |   ≥55% |
| Comprovação P0     | evidência anexável na mesma janela do PASS |

**Código:** `01_source/frontend/src/utils/fiscalSprint2FinanceGate.js` — persistência `fiscal_sprint2_finance_gate_v2`, função `summarizeSprint2FinanceGateV2`, limiares `SPRINT2_FINANCE_GATE_V2_THRESHOLDS`.  
**Testes:** `fiscalSprint2FinanceGate.test.js` (Vitest).

---

## Sequência D10–D18 (resumo operacional)

| Dia | Foco principal (plano) |
| --- | ------------------------ |
| D10 | Governança emissores / matriz país–tenant |
| D11 | Conciliação fiscal pedido→documento; rollup `order_id` exportável |
| D12 | Handoff contábil (parceiro / FG-1) |
| D13 | Aceite contábil central (`POST` / `GET latest` em `routes_admin_fiscal`; ver `test_accounting_approvals_post_latest.py`) |
| D14–D16 | Fechamento, histórico, export consolidado / diff |
| D17 | Retenção + divergence-health |
| D18 | Checklist fecho Sprint 2 + riscos P1 |

**Util D11:** `fiscalD11OrderIdRollup.js` + `fiscalD11OrderIdRollup.test.js`.  
**Util D12/D13:** `fiscalSprint2D12D13Evidence.js` + `fiscalSprint2D12D13Evidence.test.js`.  
**Util D15–D17 (API + CSV):** `fiscalAccountingApprovalsHistory.js` — `fetchConsolidatedAccountingApprovals` (paginação + filtros + clamp `pageSize`), `fetchAccountingApprovalsCompare`, `fetchAccountingApprovalsDivergenceHealth` (clamp `window` / `prolonged_edges`), `postAccountingApprovalsRetention`, e helpers CSV; tudo coberto em **`fiscalAccountingApprovalsHistory.test.js`** (incl. `vi.spyOn(globalThis, "fetch")`).  
**Util D18:** `fiscalSprint2D18Content.js` + `fiscalSprint2D18Content.test.js`.

**Pacote diário / P0-1b (ZIP `management-daily` / close):** `fiscalP01bDailyPackage.js` — `buildP01bPartnerReconciliationSlice` (agregação por `partner_id`, cruzamento opcional com snapshot D11) e `appendP01bSignedZipEntries` (GET `e2e-audit-trail`, erros assinados `SPRINT3_P0_1B_E2E_ATTACH_ERROR`, anexos `SPRINT3_E2E_AUDIT_TRAIL_*` + `P0_1B_PARTNER_RECONCILIATION_*`). **Testes:** `fiscalP01bDailyPackage.test.js` (Vitest: slice + `fetch` mockado em `appendP01bSignedZipEntries`).

**UI:** `FiscalManagementDailyPage.jsx`, `FiscalAccountingClosePage.jsx`, `FiscalSprint2FinanceGatePage.jsx`, `FiscalGlobalPage.jsx`, `OpsFiscalProvidersPage.jsx` (D11 fila / export).

---

## Comandos úteis (frontend)

```bash
cd 01_source/frontend
npm test -- --run
```

- O Vitest está configurado para **excluir** `e2e/` (`vite.config.js`), para não misturar com Playwright.
- E2E fiscal/ops continuam em `npx playwright test` conforme `playwright.config.ts`.

## Backend — `billing_fiscal_service` (rotas D15/D16)

Rotas em `app/api/routes_admin_fiscal.py` (`GET /admin/fiscal/accounting-approvals`, `GET .../compare`, etc.), consumidas pelo frontend com token interno.

```bash
cd 01_source/backend/billing_fiscal_service
PYTHONPATH=. .venv/bin/pytest tests/test_accounting_approvals_*.py -q
```

- **`tests/test_accounting_approvals_list_compare.py`:** listagem paginada (items + `total`); filtros **`owner`** (LIKE `%…%`), **`status`**, **`date_from`** / **`date_to`** (trim); compare vazio, últimos dois snapshots, **`current_id`/`previous_id`** com `WHERE id = :id` (diff `approval.owner`).
- **`tests/test_accounting_approvals_retention_divergence.py`:** `divergence-health` (menos de 2 snapshots; par com `edges` e política); `retention` dry-run com `max_deletable` 0; validação **`older_than_days`** e **`keep_minimum`** fora do intervalo → HTTP 400.
- **`tests/test_accounting_approvals_post_latest.py`:** `post_accounting_approval` (INSERT + id `faa_*`); `get_latest_accounting_approval` vazio vs round-trip após POST; `eta` inválido → HTTP 400.
- **`tests/test_accounting_approvals_d17.py`:** helpers de diff / fingerprint / `payload_json` (já existente).

---

## Registo de incrementos (lab)

| Data       | Incremento |
| ---------- | ---------- |
| 2026-04-30 | Vitest `fiscalSprint2FinanceGate.test.js` — `clampSprint2GatePct`, `summarizeSprint2FinanceGateV2`, `loadSprint2FinanceGateV2State`. |
| 2026-04-30 | Vitest `fiscalSprint2D18Content.test.js` — closeout D18, storage, payload diário vs executivo. |
| 2026-04-30 | Vitest `fiscalAccountingApprovalsHistory.test.js` — export CSV D16 (linhas + escape). |
| 2026-04-30 | Vitest mesmo ficheiro — `fetch` mockado: paginação consolidada D15/D16, filtros query, clamp `limit`, erro `!ok`, compare, divergence-health, retention POST. |
| 2026-04-30 | Vitest mesmo ficheiro — `!ok` em compare, divergence-health e retention; `POST` com `body: null` → `{}`. |
| 2026-04-30 | Backend `tests/test_accounting_approvals_list_compare.py` — `list_accounting_approvals` + `compare_accounting_approval_snapshots` com sessão SQL fake (paridade rotas vs frontend). |
| 2026-04-30 | Backend `tests/test_accounting_approvals_retention_divergence.py` — `get_accounting_approvals_divergence_health` e `post_accounting_approvals_retention` (dry-run + validação). |
| 2026-04-30 | Backend `tests/test_accounting_approvals_post_latest.py` — `post_accounting_approval` + `get_latest_accounting_approval` (DB fake, validação `eta`). |
| 2026-04-30 | Vitest `fiscalP01bDailyPackage.test.js` — slice P0-1b por parceiro, `d11_cross_check`, truncagem de batches (80). |
| 2026-04-30 | Vitest mesmo ficheiro — `appendP01bSignedZipEntries`: URL `e2e-audit-trail`, erro rede, HTTP !ok, sucesso (ZIP keys). |
| 2026-04-30 | Backend `list_accounting_approvals` — teste de filtro `owner` (padrão `%` após trim); `retention` — `keep_minimum` inválido → 400. |
| 2026-04-30 | Backend `list_accounting_approvals` — `status` + `date_from`/`date_to` nos params; `compare` com ids explícitos `snap-cur` / `snap-prev`. |
| 2026-04-30 | `vite.config.js` — `test.exclude` inclui `**/e2e/**` para `npm test` estável. |

Atualizar a tabela acima quando houver novo commit relevante à Sprint 2.

---

## Próximos passos sugeridos (prioridade)

1. **Fiscal / D10:** matriz de emissores em `OpsFiscalProvidersPage` e/ou `billing_fiscal_service` — runbook `docs/runbooks/FISCAL_CATALOGO_SEM_UI_POR_PAIS.md`.
2. **Backend:** `pytest` com DB real ou container para `retention` com `dry_run: false` e linhas elegíveis a DELETE (hoje só dry-run / limites).
3. **Plano:** checkpoint comité → percentuais Sprint 2 + linha na tabela **Registo de incrementos** acima e **Metodo** em `PLANO_30_DIAS_GLOBAL_POR_PERSONA.md`.

### Cobertura de testes (Sprint 2 — referência rápida)

| Ficheiro | Stack | Foco |
| -------- | ----- | ---- |
| `fiscalSprint2FinanceGate.test.js` | Vitest | Gate v2: limiares, nota P0, `localStorage` |
| `fiscalSprint2D18Content.test.js` | Vitest | D18 closeout, checklist, scope diário vs executivo |
| `fiscalD11OrderIdRollup.test.js` | Vitest | D11 rollup `order_id` |
| `fiscalSprint2D12D13Evidence.test.js` | Vitest | D12/D13 payloads e wrapper |
| `fiscalAccountingApprovalsHistory.test.js` | Vitest | D15–D17: CSV, `fetch` mockado (list/compare/health/retention, `!ok`) |
| `fiscalP01bDailyPackage.test.js` | Vitest | P0-1b: `buildP01bPartnerReconciliationSlice` + `appendP01bSignedZipEntries` (`fetch` mock) |
| `tests/test_accounting_approvals_list_compare.py` | pytest | `list_accounting_approvals`, `compare_accounting_approval_snapshots` (DB fake) |
| `tests/test_accounting_approvals_retention_divergence.py` | pytest | D17: `divergence-health`, `retention` (DB fake) |
| `tests/test_accounting_approvals_post_latest.py` | pytest | D13/D14: `post_accounting_approval`, `get_latest_accounting_approval` |
| `tests/test_accounting_approvals_d17.py` | pytest | Diff / fingerprint / `payload_json` |

---

## Ligações rápidas no plano

- **Backlog P0/P1** fiscal e contábil: `PLANO_30_DIAS_GLOBAL_POR_PERSONA.md` → secção *Backlog detalhado Sprint 2*.
- **Critério gate v2** e comprovação: mesma secção Sprint 2, subsecção *Critério numérico «financeiro suficiente»*.
