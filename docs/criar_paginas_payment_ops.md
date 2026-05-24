# OPS — Payments Admin (cross-domain)

## Backend (`payments_admin_service` :8126)

### Ledger (migração 001)
- `payment_transactions`, `payment_instructions`, `payment_splits`, `payments`
- `webhook_endpoints`, `gateway_events`

### Cross-domain (migração 002)
- `payment_ecosystem_player` — players mundiais (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Worten, El Corte Inglés, …)
- `payment_player_relation` — grafo cross-domain (WHITE_LABEL, CHANNEL_USES_CARRIER, AGGREGATES…)

### Ecossistema profissional (migração 004)
- `payment_ecosystem_segment` — taxonomia: LOCKER_NETWORK, LOCKER_NETWORK_OPERATOR, CARRIER_LAST_MILE, MARKETPLACE, COLLECTION_POINT, LOGISTICS_PLATFORM, FOOD_DELIVERY, PAYMENTS_FISCAL
- `payment_player_country_coverage` — cobertura país×player (densidade, mercado primário)
- `payment_player_integration` — readiness, protocolo, capture mode, domínios ligados

**Players extras** (`world_locker_payment_players_extended.py`): Yodel, Swiss Post, Australia Post, Bring, PostNord, Parcel2Go, iFood, Rappi, Mercado Pago, Rakuten, Flipkart, etc.

**Integração por segmento:** `GET /player-integrations/playbook/{segment_code}` (passos + domínios order_pickup, finance, marketplace, fiscal).

### Hub cross-domain (migração 006) — PAYMENT ↔ outros domínios

- `payment_domain_registry` — catálogo (ORDER_PICKUP, FINANCE, MARKETPLACE, FISCAL, PAYMENT_GATEWAY, MONEY_CAMBIO, RUNTIME, PARTNERS, BILLING_FISCAL) com deep-link OPS
- `payment_external_reference` — vínculo entidade PAYMENT ↔ ID externo (NF, shipment, gateway session, settlement…)
- `payment_domain_obligation` — obrigações por domínio (emitir NF, hold financeiro, confirmar pickup) com flag `blocking_payment`
- `payment_cross_domain_event` — outbox de eventos para propagar a outros domínios

| API | Uso |
|-----|-----|
| `/cross-domain/registry` | Domínios integrados |
| `/cross-domain/external-references` | CRUD vínculos |
| `/cross-domain/obligations` | CRUD obrigações |
| `/cross-domain/events` | Fila de eventos + `publish` |
| `/cross-domain/gaps` | Scanner de lacunas (ref ausente, tx ausente, obrigação bloqueante) |
| `/cross-domain/order-360/{order_id}` | Visão 360° por pedido com links OPS |

### Funcionalidades de valor (migração 005) — além do escopo original
- `payment_integration_milestone` — roadmap DISCOVERY → PRODUCTION por player
- `payment_settlement_corridor` — corredores FX/settlement cross-border (BR→PT, CN→BR, …)
- `payment_player_compliance` — LGPD, GDPR, PCI, risk tier por país
- `payment_routing_rule` — roteamento inteligente (país + método → PSP primário/fallback)
- `payment_integration_incident` — incidentes de integração (SLA, webhooks, rate limit)

**Inteligência extra:**
- `GET /intelligence/global-readiness` — dashboard executivo mundial
- `GET /intelligence/ecosystem-graph` — nós/arestas para visualização do grafo
- `GET /intelligence/routing-suggest?country_code=BR&payment_method=PIX` — simulador de roteamento
- `payment_order_context` — vínculo pedido ↔ tenant, locker, marketplace, carrier
- `payment_context_player_link` — grafo de players por pedido
- `payment_reconciliation_batch` — lotes de conciliação
- `webhook_deliveries` — fila/DLQ de entregas
- `partner_payment_holds` — retenções (ligação Finance)
- `saved_payment_methods` — vault tokenizado

### APIs
| Prefixo | Recursos |
|---------|----------|
| `/ecosystem-players` | CRUD catálogo mundial (sync `money_cambio` quando disponível) |
| `/ecosystem-segments` | Taxonomia de segmentos |
| `/player-integrations` | Perfis de integração + playbook por segmento |
| `/player-country-coverage` | Cobertura geográfica |
| `/player-relations` | Grafo de relações entre players |
| `/order-context` | CRUD + `by-order/{order_id}` |
| `/reconciliation-batches` | CRUD + `assign-transactions` |
| `/webhook-deliveries` | list + `retry` |
| `/partner-holds` | CRUD |
| `/saved-payment-methods` | list/create/deactivate |
| `/intelligence/summary` | KPIs |
| `/intelligence/order-graph/{order_id}` | grafo completo PAYMENT |
| `/integration-milestones` | Roadmap integração (CRUD) |
| `/routing-rules` | Regras de roteamento (CRUD) |
| `/settlement-corridors` | Corredores settlement/FX |
| `/player-compliance` | Compliance regulatório |
| `/routing-rules` | Regras de roteamento |
| `/integration-incidents` | Incidentes abertos/resolvidos |
| `/intelligence/global-readiness` | KPIs executivos |
| `/intelligence/ecosystem-graph` | Grafo players+relações |
| `/intelligence/routing-suggest` | Simulador PSP |

```bash
cd 01_source/payments_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8126 --reload
```

## Frontends

- **v1** `/v1/ops/payments/admin` — abas: inteligência (+ simulador roteamento), **grafo React Flow**, ecossistema, …; CRUD inline em **Roadmap** e **Roteamento** (POST/PATCH/DELETE).
- Dependência v1: `@xyflow/react` (já em v0).
- **v0** `/v0/ops/payments/admin` — mesmo contrato, shell OPS

Menu: grupo **Payments OPS** (separado de Payment Gateway :8017 e Money :8125) — entradas em `Menu.tsx`, `Sidebar.tsx` (v1) e `App.jsx` (v0) para todas as abas: grafo, segmentos, integrações, cobertura, roadmap, corredores, compliance, roteamento, incidentes, ledger, etc.

Seed demo: `ORD-DEMO-INPOST-001` com Magalu × DPD × InPost × Melhor Envio.
