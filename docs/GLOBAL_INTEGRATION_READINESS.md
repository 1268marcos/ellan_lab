# Prontidão de integração global (Marketplace + ML)

## Objetivo

Score 0–100 e faixa operacional (**GO_LIVE**, **PILOT**, **PLANNED**, **BLOCKED**) por player de canal e por rede locker ML — com incidentes, auditoria e KPIs no dashboard OPS.

## Marketplace (`marketplace_admin_service`)

| Tabela | Função |
|--------|--------|
| `marketplace_integration_readiness` | Score por `channel_partner_id` |
| `marketplace_integration_incidents` | Incidentes abertos (API, certificado, rate limit) |
| `marketplace_sync_audit_log` | Trilha de seed e recompute |

**API**

- `GET /integration-hub/summary`
- `GET /integration-readiness?band=GO_LIVE`
- `POST /integration-readiness/recompute`
- `GET /integration-incidents`
- `GET /sync-audit-log`

O `POST /channel-partners/seed-players` recalcula prontidão automaticamente.

## ML Admin (`ml_admin_service`)

| Tabela | Função |
|--------|--------|
| `ml_integration_readiness_snapshots` | Score por rede locker |
| `ml_ops_audit_log` | Auditoria de recompute / seed |

**API**

- `GET /ml-readiness-hub/summary`
- `GET /ml-integration-readiness`
- `POST /ml-integration-readiness/recompute`

O seed de redes locker recalcula snapshots ML.

## UI

- Marketplace v0: aba **Prontidao integracao**
- ML v0: aba **Prontidao ML**

## Migrations

- `marketplace_admin_service/migrations/005_integration_readiness.sql`
- `ml_admin_service/migrations/005_ml_integration_readiness.sql`
