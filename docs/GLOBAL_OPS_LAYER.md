# Camada Global OPS — certificações, corredores e prontidão

Extensão profissional do ecossistema Partner / Marketplace para operação **mundial** (compliance, rotas cross-border, scores por player, saúde em cascata no grafo).

## Tabelas

| Serviço | Tabela | Uso |
|---------|--------|-----|
| Partner | `partner_player_certifications` | ISO27001, LGPD_DPA, SOC2, PCI por player |
| Partner | `partner_global_corridors` | Rota origem→destino + primary/fallback player |
| Partner | `partner_ecosystem_readiness` | Score 0–100 e faixa por `ecosystem_player` |
| Partner | `partner_relation_health` | HEALTHY / DEGRADED / OUTAGE nas relações do grafo |
| Marketplace | `marketplace_player_certifications` | Espelho comercial (channel partners) |
| Marketplace | `marketplace_global_corridors` | Corredores para sellers / OPS |
| Marketplace | `marketplace_corridor_player_steps` | Cadeia multi-hop (ex. CTT → SEUR) |

## Migração 007

```bash
cd 02_docker/postgres_central/ops
./apply_partner_ecosystem_migrations.sh   # inclui 007_partner_global_ops.sql
./apply_marketplace_admin_migrations.sh # inclui 007_marketplace_global_ops.sql
```

## API Partner (`/api/v1/partner-admin/ecosystem/global-ops`)

| Método | Path |
|--------|------|
| GET | `/summary` |
| POST | `/seed` |
| POST | `/recompute-readiness` |
| POST | `/recompute-relation-health` |
| GET | `/certifications?player_code=INPOST` |
| GET | `/corridors?origin=BR&dest=DE` |
| GET | `/readiness?band=GO_LIVE` |
| GET | `/relation-health?status=DEGRADED` |

`POST /ecosystem/players/seed-professional` também dispara `global_ops.seed`.

## API Marketplace (`/api/v1/marketplace-admin/global-ops/...`)

| Método | Path |
|--------|------|
| GET | `/global-ops/summary` |
| POST | `/global-ops/seed` |
| GET | `/global-ops/certifications` |
| GET | `/global-ops/corridors` (inclui `steps[]`) |

## Corredores seed (exemplos)

- `BR-BR-LOCKER-NATIONAL` — Correios + fallback Jadlog  
- `BR-EU-CROSSBORDER` — DHL → InPost  
- `PT-ES-IBERIA` — CTT → SEUR  
- `EU-EU-LOCKER-MESH` — InPost → DPD  
- `BR-MARKETPLACE-FULFILL` — ML / Magalu → rede locker  

## Migração 008 (DLQ, SLA, espelho certificações)

```bash
./apply_partner_ecosystem_migrations.sh   # 008_partner_webhook_dlq_...
./apply_marketplace_admin_migrations.sh   # 008_marketplace_webhook_dlq_...
```

### Dead-letter webhook (capability)

Após **3 falhas** consecutivas no mesmo webhook, a entrega vai para `DEAD_LETTER`.

| Serviço | Endpoints |
|---------|-----------|
| Partner | `GET/POST .../ecosystem/capability-webhooks/deliveries` |
| Partner | `POST .../deliveries/{id}/replay` |
| Partner | `POST .../deliveries/replay-dead-letter?limit=25` |
| Marketplace | `GET/POST .../capability-webhooks/deliveries` (mesmos paths sob marketplace-admin) |

### SLA por corredor

Tabela `partner_corridor_sla` / `marketplace_corridor_sla`: uptime %, on-time %, `max_transit_hours`, latência P95 webhook, `compliance_status` (`COMPLIANT` / `AT_RISK` / `BREACH`).

- `GET .../global-ops/corridor-sla`
- Incluído no `POST .../global-ops/seed`

### Espelho certificações (mesmo `locker_central`)

| Direção | Campo de vínculo | `source` |
|---------|------------------|----------|
| Marketplace → Partner | `partner_player_certifications.marketplace_certification_id` | `MARKETPLACE_MIRROR` |
| Partner → Marketplace | `marketplace_player_certifications.partner_certification_id` | `PARTNER_MIRROR` |

- `POST /ecosystem/global-ops/certifications/mirror` (Partner, bidirecional)
- `POST /global-ops/certifications/mirror` (Marketplace, a partir do Partner)

Requer `partner_ecosystem_players.marketplace_channel_id` preenchido (sync catálogo). No `locker_central`, rode **ambos** os seeds e depois o mirror Partner.

### Dead-letter (3 falhas → `DEAD_LETTER`)

Campos em `*_capability_webhook_deliveries`: `status`, `attempt_count`, `dead_lettered_at`, `replay_of_delivery_id`.

| `status` | Significado |
|----------|-------------|
| `DELIVERED` | HTTP 2xx |
| `FAILED` | Falha, ainda pode repetir |
| `DEAD_LETTER` | 3ª falha consecutiva — fila morta |
| `SKIPPED` | Evento não assinado |

### SLA por corredor

`partner_corridor_sla` / `marketplace_corridor_sla`: uptime alvo, on-time %, `max_transit_hours`, latência P95 webhook, `compliance_status`.

## UI

- Partner OPS → aba **Redes mundiais** → **Seed Global OPS**, **Replay dead-letter**  
- Marketplace OPS → aba **Prontidão integração** → **Seed Global OPS**

## Score de prontidão (Partner)

| Componente | Máx | Critério |
|------------|-----|----------|
| Certificações | 25 | +8 por cert VALID |
| Capabilities | 35 | production_ready + sandbox |
| Corredores | 20 | participação primary/fallback |
| Webhooks | 20 | HTTP 2xx recente na capability webhook |

Faixas: `GO_LIVE` ≥75 sem blockers · `PILOT` ≥50 · `PLANNED` ≥25 · `BLOCKED` caso contrário.
