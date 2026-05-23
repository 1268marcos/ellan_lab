# Finance Admin — runbook local

## Backend (porta 8023)

```bash
cd 01_source/finance_admin_service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8023 --reload
```

Se as abas OPS mostrarem **Not Found**, o processo na 8023 está desatualizado (sem rotas `billing-line-items`, `locker-network-catalog`, etc.). Pare o uvicorn antigo e suba de novo a partir de `finance_admin_service`, depois:

```bash
curl -X POST http://localhost:8023/api/v1/finance-admin/seed
```

## Testes

```bash
cd 01_source/finance_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontends

- v1: proxy `/api/finance-admin` → `:8023` — rota `/ops/finance/admin`
- v0: proxy `/api/fna` → `:8023` — rota `/ops/finance/admin`

## Seed

`POST /api/v1/finance-admin/seed` ou `SEED_ON_START=true`

## Domínio estendido (v0.2)

Tabelas adicionais (migration `002_finance_extended.sql`):

| Área | Tabelas |
|------|---------|
| Billing | `partner_billing_line_items` |
| Settlements | `partner_settlement_batches`, `partner_settlement_items` |
| Treasury | `partner_credit_notes`, `partner_payment_holds`, `partner_commission_structure` |
| PnL | `cost_centers`, `cost_center_monthly` |
| Fiscal | `fiscal_reconciliation_gaps` |
| Webhooks | `partner_webhook_deliveries` |

Abas UI: **networks** · partners · billing · invoices · settlements · treasury · wallet · pnl · reconciliation · webhooks · ops

## Catálogo mundial locker (`finance_locker_network_catalog`)

Fonte: `app/data/global_locker_finance_catalog.py` — 50+ players (InPost, DHL, Magalu, Mercado Livre, Amazon BR/US/ES, DPD, Correios, CTT, Worten, El Corte Inglés, SwipBox, Cleveron, Cainiao, USPS, Royal Mail, etc.)

```bash
curl -X POST http://localhost:8023/api/v1/finance-admin/locker-network-catalog/sync
curl http://localhost:8023/api/v1/finance-admin/locker-network-catalog?parent_group=MARKETPLACE
```

O seed (`POST .../seed`) chama sync automaticamente e cria `finance_partner_accounts` + planos para players prioritários.

## Módulo profissional (migration `005_finance_professional_ops.sql`)

| Tabela | Função |
|--------|--------|
| `partner_commercial_contracts` | MSA / contratos por parceiro |
| `finance_integration_milestones` | Roadmap DISCOVERY → LIVE |
| `finance_partner_readiness` | Score 0–100 e grade A–D |
| `partner_sla_definitions` / `partner_sla_breaches` | SLAs + crédito automático |

Endpoints: `ecosystem-summary`, `partner-readiness/recompute`, `commercial-contracts`, `integration-milestones`, `sla-definitions`, `sla-breaches`, `billing-cycles/{id}/close`, `webhook-deliveries/{id}/replay`.

Abas UI: **ecosystem** · **readiness** · **roadmap** · **contracts** · **slas** (além das 11 anteriores).

## Domínio avançado (migration `006_finance_advanced_domain.sql`)

| Área | Tabelas / endpoints |
|------|---------------------|
| Payment terms | `partner_payment_terms` — `GET/POST /payment-terms` |
| FX | `finance_fx_rates` — `GET/POST /fx-rates`, `GET /fx-rates/convert` |
| Tiers | `partner_commercial_tiers`, `partner_tier_assignments` |
| Dunning | `partner_dunning_policies`, `partner_dunning_cases`, `POST /dunning/scan` |
| Reconciliação settlement | `settlement_reconciliation_*`, `POST /settlement-batches/{id}/reconcile` |
| Corredores fiscais | `partner_tax_corridors` — usado no fechamento de ciclo (`tax_cents`) |
| Docs NF | `partner_invoice_documents` |
| Auditoria | `finance_audit_log` — `GET /audit-log` |

Menus: **Finance OPS — Comercial** (v0/v1) + abas dunning, tiers, fx, tax, documents, audit.

## Revenue recognition, fiscal live e jobs (migration `007`)

| Recurso | Detalhe |
|---------|---------|
| Diferimento local | `partner_revenue_schedules` + `partner_revenue_recognition_entries` (STRAIGHT_LINE) |
| Sync fiscal | `POST /revenue-recognition/run?sync_fiscal=true` → `billing_fiscal_service` `/admin/fiscal/revenue-recognition/recompute` |
| Emissão NF B2B | `POST /b2b-invoices/{id}/emit-fiscal` → `billing_fiscal` `/v1/partners/.../issue-fiscal` |
| Jobs | `finance_scheduled_job_runs` + APScheduler (dunning 08:00, reconcile 09:15, revrec 10:30, fiscal gap 11:45) |
| Manual | `POST /jobs/run/{code}` · `POST /jobs/run-all` |

Variáveis:

```bash
BILLING_FISCAL_BASE_URL=http://localhost:8020
BILLING_FISCAL_INTERNAL_TOKEN=dev-internal-token
BILLING_FISCAL_LIVE_ENABLED=true   # false = stub local
ENABLE_FINANCE_SCHEDULER=true
```

Abas UI: **revrec** · **jobs** (+ emitir NF na aba invoices).
