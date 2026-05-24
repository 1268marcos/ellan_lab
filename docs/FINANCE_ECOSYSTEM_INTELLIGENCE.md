# Ecosystem Intelligence — FINANCE OPS

Módulo de **valor agregado** (não previsto no MVP): detecta gaps, ranqueia players, monitora saúde de integração e gera roadmap automático.

## Tabelas (`010_finance_ecosystem_intelligence.sql`)

| Tabela | Função |
|--------|--------|
| `finance_ecosystem_insights` | Gaps/oportunidades (MISSING_CARRIER_LINK, LOW_READINESS, ORPHAN_PLAYER…) |
| `finance_player_benchmarks` | Ranking composite por segmento (readiness + relações + capabilities) |
| `finance_integration_health_checks` | Saúde API_DOCS / FINANCE_LINK / BLUEPRINT por player LIVE/PILOT |

## API (`/api/v1/finance-admin/ecosystem-intelligence`)

```bash
curl -X POST http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/analyze
curl http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/dashboard
curl http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/insights?severity=HIGH
curl http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/benchmarks?limit=20
curl http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/recommendations/MAGALU
curl -X POST http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/generate-milestones/INPOST
curl -X POST http://localhost:8123/api/v1/finance-admin/ecosystem-intelligence/insights/{id}/resolve
```

## Jobs agendados

| Job | Cron (default) | Ação |
|-----|----------------|------|
| `READINESS_RECOMPUTE` | 06:00 | Score por blueprint |
| `ECOSYSTEM_INTELLIGENCE_SCAN` | 06:30 | analyze + benchmarks + health + milestones demo |

Manual: aba **Jobs** ou `POST /jobs/run/ECOSYSTEM_INTELLIGENCE_SCAN`

## UI

**Finance OPS → Inteligência**: dashboard, insights com ação Resolver, top benchmarks, botão **Scan inteligência**.

## Tipos de insight

- `MISSING_CAPABILITIES` — player ativo sem capabilities
- `MISSING_CARRIER_LINK` — marketplace sem carrier
- `MISSING_COVERAGE` — prioritário sem cobertura país
- `MISSING_FINANCE_PARTNER` — sem conta billing
- `LOW_READINESS` — grade C/D
- `NO_BLUEPRINT` — segmento sem blueprint
- `ORPHAN_PLAYER` — tier global sem relações

## Recomendações

Endpoint `/recommendations/{code}` sugere carriers (CORREIOS, INPOST), agregadores (Melhor Envio, Sendcloud) e ações (readiness, cobertura).
