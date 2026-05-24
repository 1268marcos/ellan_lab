# Fiscal Intelligence (fiscal_admin_service)

Módulo OPS que detecta riscos fiscais antes da emissão falhar em produção.

## Endpoints (`/api/v1/fiscal-admin/fiscal-intelligence`)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/dashboard` | KPIs: insights abertos, certs expirando, DLQ, contingências |
| POST | `/analyze` | Scan e upsert de insights |
| GET | `/insights` | Lista insights (`status=OPEN`) |
| GET/POST | `/contingency-events` | Histórico e registro de contingência SEFAZ |
| POST | `/contingency-events/{id}/close` | Encerrar contingência |
| POST | `/seed-demo` | Demo: cert A1 a expirar em 45d |

## Extensões global-ops

- `GET /corridors/{code}` — regras ICMS/IVA do corredor
- `GET /certifications?enriched=true` — `expiry_severity`, `days_until_expiry`
- `POST /webhook-deliveries/{id}/retry` — reenfileirar DLQ
- `POST /classification-rules/test-classify?sku=...` — simular NCM/CFOP

## UI

`/ops/fiscal/admin?tab=intelligence` — scan, contingência, KPIs e insights.

## Workbench de gaps (admin + billing)

`GET /fiscal-ops/reconciliation-gaps/workbench` agrega:

- **admin** — gaps do `fiscal_admin_service` (demo/catálogo OPS)
- **billing** — gaps de `GET /admin/fiscal/gaps` no `billing_fiscal_service` (emissão real: `PAID_WITHOUT_INVOICE`, etc.)

Resolver: `PATCH .../workbench/{id}?source=admin|billing`

Variáveis: `BILLING_FISCAL_BASE_URL`, `BILLING_FISCAL_INTERNAL_TOKEN`, `BILLING_FISCAL_LIVE_ENABLED` (default `true` no fiscal admin).

UI: `/ops/fiscal/admin?tab=gaps`

## Tipos de insight

- `cert_expiring` — A1/homologação a vencer
- `webhook_dlq_backlog` — falhas de entrega
- `readiness_low` — band C/D
- `corridor_no_fallback` — cross-border sem fallback
- `reconciliation_gap_high` — gap OPEN HIGH
- `contingency_active` — SEFAZ em modo contingência
