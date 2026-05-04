# 🧠 ELLAN LAB — Cursor/Claude System Prompt
> Cole este arquivo como contexto inicial de cada sessão. Não re-explique o projeto — referencie este doc.

---

## IDENTIDADE DO PROJETO

**Serviço:** `order_pickup_service` (OPS) — migração de monolito (~15k linhas) para microserviços.
**Stack:** Python 3.11 · FastAPI · SQLAlchemy (async) · PostgreSQL · Redis Streams → Kafka · Pydantic v2 · pytest · mTLS (opcional via `MTLS_ENFORCE=1`).
**Padrão arquitetural:** DDD + Strangler Fig + Event-Driven (consistência eventual).
**Repo base:** `01_source/`

---

## ESTADO ATUAL (o que JÁ existe — não recriar)

| Serviço | Status | Caminho | Pendente no monolito |
|---|---|---|---|
| `partner-service` | 🟡 45% | — | Roteamento `/partners/*` no API Gateway |
| `catalog-service` | ✅ 100% | `01_source/catalog_service` | — |
| `inventory-service` | ✅ 100% | `01_source/inventory_service` | Integração HTTP com OPS |
| `notification-service` | ✅ 90% | `01_source/notification_service` | OPS ainda enfileira localmente |
| `wallet-service` | ✅ 90% | `01_source/wallet_service` | Double-write + consumo pelo OPS |
| `logistics-service` | ✅ 90% | `01_source/logistics_service` | Runbooks + remoção `logistics.py` do OPS |
| **Trilha A (Infra/Kafka)** | 🟠 80% | `inventory_service/infra/kafka` | Topics: `wallet-stream`, `notification-stream` |
| **Trilha B (mTLS)** | 🟡 55% | `inventory_service/infra/mtls` | Enforce nos novos serviços |
| **Trilha C (Observabilidade)** | 🟡 70% | `trilhas_sprint4/` | Grafana/Prometheus dashboards SLO |

### Feature Flags no OPS (`app/core/config.py → Settings`)
```
USE_CATALOG_SERVICE=false   # ativar após catalog pronto
USE_PARTNER_SERVICE=true
USE_INVENTORY_SERVICE=true
USE_WALLET_SERVICE=true
USE_LOGISTICS_SERVICE=true
SHADOW_MODE_ENABLED=false
```

---

## BOUNDED CONTEXTS — DONO DE CADA DOMÍNIO

| Domínio | Dono | OPS faz |
|---|---|---|
| SKU / catálogo | `catalog-service` | GET + consume eventos |
| Estoque físico | `inventory-service` | POST reserve/consume |
| Parceiros + webhooks | `partner-service` | GET parceiro |
| Créditos / wallet | `wallet-service` | GET saldo, POST aplicar |
| Notificações | `notification-service` | Enfileirar apenas |
| Manifesto / SLA | `logistics-service` | POST manifesto |
| Hardware locker | `backend-runtime` | Delega |
| Deadlines / analytics | `order-lifecycle-service` | Delega |
| Emissão fiscal | `billing-fiscal-service` | Delega |

**Regra de ouro:** O OPS **orquestra**, nunca persiste dados de domínio alheio.

---

## CONTRATOS CANÔNICOS

### DTO de produto (imutável entre serviços)
```python
# OrderPickupProductCacheDTO — catalog-service → OPS
sku_id, partner_id, partner_sku, name, category_id,
amount_cents, currency, width_mm, height_mm, depth_mm,
weight_g, is_active, requires_signature, is_hazardous,
temperature_zone, created_at, updated_at, synced_at
```

### Eventos Redis Streams / Kafka
```
product.created · product.price_changed · product.deprecated
payment.confirmed → inventory-service consume
order.expired    → inventory-service consume
manifest.created → logistics-stream
wallet-stream · notification-stream
```

### Cache local (OPS) — `products_cache`
TTL Redis: 5 min · Invalidação: evento `product.*` · Prefixo DB: `catalog_`, `partner_`, `inventory_`, `wallet_`.

---

## ESTRATÉGIA DE MIGRAÇÃO (não mudar sem justificativa)

```
Fase 0 → Shadow mode (novos serviços só loggam)
Fase 1 → Feature flag por parceiro
Fase 2 → Canário: 5% → 25% → 50% → 100%
Fase 3 → Remoção do código morto
```

**Rollback:** feature flag reverte em < 1 min. Trigger automático: error rate > 0.5% por 5 min.

**Versionamento:** `/v1/` → monolito (deprecação 2026-12-31) · `/v2/` → microserviços.

---

## PENDÊNCIAS PRIORITÁRIAS (próximas sprints)

### 🔴 Sprint 1 — `partner-service` (completar 45% → 100%)
- [ ] Finalizar CRUD completo em `partner-service` (base: `app/routers/partners.py` do OPS, ~5k linhas)
- [ ] API Gateway: rotear `/partners/*` → `partner-service`
- [ ] Shadow mode ativo por 1 semana antes de ligar `USE_PARTNER_SERVICE=true`
- [ ] Validar com 1 parceiro piloto (baixo volume)

### 🟠 Sprint 4/5 — Integração OPS ↔ Novos Serviços (pendente no monolito)
- [ ] OPS HTTP client → `inventory-service` (`POST /reserve`, `POST /consume`)
- [ ] OPS enfileirar notificações → `notification-service` (remover `notification_delivery_worker.py`)
- [ ] OPS double-write → `wallet-service` + consumo de saldo
- [ ] Remover do OPS: `logistics.py`, `notification_delivery_worker.py`, `credits_domain.py`

### 🟡 Trilhas Paralelas
- [ ] **Trilha A:** Finalizar consumers `wallet-stream` + `notification-stream`
- [ ] **Trilha B:** mTLS enforce em `notification-service`, `wallet-service`, `logistics-service`
- [ ] **Trilha C:** Dashboards SLO (error rate por parceiro, divergência, latência p95)
- [ ] Runbooks de operação (rollback, reconciliação, on-call)
- [ ] Comunicação a parceiros: depreciação `/v1/` com 90 dias de antecedência

---

## PADRÕES DE CÓDIGO (seguir sempre)

```python
# 1. Novos serviços: estrutura padrão
app/
  routers/          # FastAPI routers
  services/         # regras de negócio
  models/           # SQLAlchemy models
  schemas/          # Pydantic DTOs
  infra/
    kafka/          # producers, consumers, topics
    mtls/           # middleware opcional

# 2. Idempotência obrigatória em consumers Kafka
# 3. DLQ (Dead Letter Queue) em todos os workers
# 4. Lock otimista em reservas de inventário
# 5. Health checks obrigatórios: GET /health/ready + GET /health/live
# 6. Feature flag antes de qualquer mudança de roteamento no OPS
# 7. Shadow mode ANTES de feature flag = true
# 8. Prefixo de tabelas: catalog_, partner_, inventory_, wallet_ (Fase 1 DB)
```

### Anti-patterns — NUNCA fazer
```
❌ OPS persistir dados de produto, parceiro, crédito ou estoque como master
❌ Remover código do monolito sem feature flag + canário estável
❌ Novo serviço sem /health/ready e /health/live
❌ Consumer Kafka sem DLQ
❌ Mudança no DTO OrderPickupProductCacheDTO sem versionar
❌ Teste de integração sem cleanup de dados
```

---

## SLOs — CRITÉRIOS DE DONE

```yaml
Error rate:          < 0.1%  vs baseline
Latência p95:        < baseline + 10ms
Divergência dados:   < 0.01% dos pedidos
Rollback automático: < 1 min após trigger
Canário estável:     2 semanas sem incidente → remoção do código antigo
```

---

## COMO USAR ESTE PROMPT

**Início de sessão:** Cole este arquivo + descreva a tarefa específica da sprint.
**Durante a sessão:** Referencie caminhos (`01_source/inventory_service/...`) em vez de colar código.
**Ao pedir código:** Especifique serviço-alvo, endpoint/evento e se é nova feature ou integração com OPS.
**Ao fazer perguntas de arquitetura:** Consulte a seção "Bounded Contexts" antes de perguntar ao modelo.

### Exemplos de prompt eficiente
```
# ✅ Bom (específico, referenciado)
"Implementar HTTP client no OPS para chamar POST /inventory/reserve.
Base: 01_source/inventory_service/app/routers/inventory.py.
Seguir padrão de feature flag USE_INVENTORY_SERVICE."

# ❌ Ruim (vago, força o modelo a inferir contexto)
"Integrar o serviço de inventário com o sistema de pedidos"
```

---

> **Próximo passo imediato:** Finalizar `partner-service` (Sprint 1) →
> Criar repo, copiar `partners.py`, rodar shadow mode, validar 1 parceiro.
