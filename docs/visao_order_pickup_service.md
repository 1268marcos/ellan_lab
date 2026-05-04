# Visão Arquitetural — `order_pickup_service`
**Projeto:** ELLAN LAB | **Status:** Aprovado para implementação

---

## Índice

1. [Diagnóstico do Problema](#1-diagnóstico-do-problema)
2. [Arquitetura Alvo](#2-arquitetura-alvo)
3. [Bounded Contexts (DDD)](#3-bounded-contexts-ddd)
4. [Solução Técnica](#4-solução-técnica)
5. [Modelo de Dados](#5-modelo-de-dados)
6. [Contratos de API](#6-contratos-de-api)
7. [Estratégia de Migração](#7-estratégia-de-migração)
8. [Plano de Implementação (Sprints)](#8-plano-de-implementação-sprints)
9. [Versionamento de API](#9-versionamento-de-api)
10. [Matriz de Risco](#10-matriz-de-risco)
11. [Métricas de Sucesso (SLOs)](#11-métricas-de-sucesso-slos)
12. [Estratégia de Banco de Dados](#12-estratégia-de-banco-de-dados)
13. [Definição Final do Serviço](#13-definição-final-do-serviço)
14. [Checklist de Prontidão](#14-checklist-de-prontidão)

---

## 1. Diagnóstico do Problema

### 1.1 O Problema Central

> **O `order_pickup_service` está tentando ser dono do produto, quando deveria ser apenas um consumidor do catálogo.**

A gestão de produtos está **fundamentalmente incorreta**. O problema não é apenas "falta um endpoint" — é uma **falha de arquitetura** que mistura conceitos de:

- **Cadastro de produto** (deveria ser centralizado, multi-tenant)
- **Catálogo público** (deveria ser um serviço separado)
- **Compatibilidade locker-produto** (regras de negócio)
- **Inventário físico** (quantidade por slot/locker)

### 1.2 Violação do Single Responsibility Principle

O `order_pickup_service` atual é responsável por **10 domínios diferentes**:

| Responsabilidade | Status |
|---|---|
| Gestão de pedidos | ✅ Correto — era para ser isso |
| Gestão de pickups/retiradas | ✅ Correto |
| Gestão de inventário físico | ❌ Deveria ser outro serviço |
| Gestão de créditos e wallets | ❌ Deveria ser outro serviço |
| Emissão de documentos fiscais simulados | ❌ Deveria ser apenas delegate |
| Webhooks de parceiros | ❌ Deveria ser outro serviço |
| Workers de reconciliação | ❌ Deveria ser outro serviço |
| Notificações (email/SMS/WhatsApp) | ❌ Deveria ser outro serviço |
| Integração com runtime (hardware) | ❌ Já existe `backend_runtime` para isso |
| Gestão de parceiros (CRUD complexo) | ❌ Deveria ser outro serviço |

### 1.3 Evidências no Código

**Gestão de Parceiros** — ~~`app/routers/partners.py`~~ removido do monólito; referência histórica (~2.500+ linhas no legado):
```python
class PartnerApiKey(Base): ...
class PartnerServiceArea(Base): ...
class PartnerSettlementBatch(Base): ...
class PartnerPerformanceMetric(Base): ...
# Sistema de partner management completo dentro do serviço de pedidos.
```

**Gestão de Créditos e Wallet** — `app/services/wallet_credits_bridge.py` (legado no monólito; alvo `wallet-service`):
```python
class Credit(Base): ...
def apply_credit_for_checkout(...): ...
def grant_expired_pickup_credit(...): ...
# Sistema financeiro dentro do serviço.
```

**Inventário Físico** — ~~`app/routers/inventory.py`~~ removido do monólito; referência histórica:
```python
class ProductInventory(Base): ...
class ProductLockerConfig(Base): ...
def post_inventory_reserve(...): ...
def post_inventory_restock(...): ...
# Sistema de WMS (Warehouse Management) dentro do serviço.
```

**Webhooks e Entregas** — `app/workers/partner_webhook_delivery_worker.py`:
```python
class PartnerWebhookDelivery(Base): ...
def _deliver_one(...): ...
# Sistema de webhook gateway dentro do serviço.
```

**Notificações Multi-canal** — ~~`app/workers/notification_delivery_worker.py`~~ removido; filas/canais via `app/services/notification_dispatch_service.py` e `notification-service`:
```python
def queue_pickup_email(...): ...
def queue_pickup_sms(...): ...
def queue_pickup_whatsapp(...): ...
# Serviço de notificações dentro do serviço.
```

### 1.4 Tamanho do Monolito

| Arquivo | Linhas | O que faz |
|---|---|---|
| ~~`partners.py`~~ | — | Migrado para `partner-service` (router removido do monólito) |
| ~~`logistics.py`~~ | — | Migrado para `logistics-service` (router removido) |
| `pickup_payment_fulfillment_service.py` | 1.500+ | Fluxo completo KIOSK + ONLINE |
| ~~`inventory.py`~~ | — | Migrado para `inventory-service` (router removido) |
| `wallet_credits_bridge.py` | 600+ | Wallet e créditos (transição) |
| `public_orders.py` | 800+ | API pública de pedidos |
| `pricing_fiscal.py` | 700+ | Promoções e regras fiscais |
| **Total estimado** | **15.000+** | **Um "ERP" em um único container** |

### 1.5 Riscos Reais

| Risco | Severidade |
|---|---|
| Violação do Single Responsibility | 🔴 Crítico |
| Tamanho do código (15k+ linhas) | 🔴 Crítico |
| Falha em cascata (tudo depende de um único serviço) | 🔴 Crítico |
| Dificuldade de escala (não dá para escalar partes individualmente) | 🟠 Alto |
| Complexidade cognitiva (novo dev precisa entender 15k linhas para qualquer mudança) | 🟠 Alto |
| Acoplamento (mudança em créditos pode quebrar pickups) | 🟠 Alto |
| Gestão de parceiros (deveria ser separado) | 🟠 Alto |
| Gestão de inventário (deveria ser separado) | 🟡 Médio |
| Gestão de créditos (deveria ser separado) | 🟡 Médio |
| Notificações (deveriam ser separadas) | 🟡 Médio |

---

## 2. Arquitetura Alvo

### 2.1 Visão Geral (Microservices)

```mermaid
graph TB
    subgraph "Camada de Orquestração"
        A[order-pickup-service<br/>Apenas fluxo pedido → pickup]
        B[order-lifecycle-service<br/>✅ Já correto]
    end

    subgraph "Camada de Domínio"
        C[catalog-service<br/>Produtos + categorias]
        D[inventory-service<br/>Estoque físico por locker]
        E[partner-service<br/>Gestão de parceiros]
        F[wallet-service<br/>Créditos e wallets]
        G[notification-service<br/>Email/SMS/WhatsApp]
        K[logistics-service<br/>Manifesto / entrega / SLA]
    end

    subgraph "Camada de Infra"
        H[backend-runtime<br/>Hardware lockers]
        I[billing-fiscal-service<br/>Notas fiscais]
        J[payment-gateway<br/>Pagamentos]
    end

    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> K
    A --> H
    A --> I
    A --> J
    K --> H
    B --> A
```

### 2.2 Comparativo: Responsabilidades Atuais vs. Corretas

| Serviço | Responsabilidade Atual | Responsabilidade Correta |
|---|---|---|
| **order_pickup_service** | Tudo: pedidos, pickups, inventário, créditos, parceiros, webhooks, notificações | Apenas orquestrar fluxo de pedido + pickup |
| **order_lifecycle_service** | Apenas deadlines e analytics | ✅ Correto |
| **logistics_service** | Hoje embutido em `logistics.py` (monólito) | Manifesto, entrega, SLA consultando lifecycle + runtime |
| **backend_runtime** | Gerenciar hardware/estado dos lockers | ✅ Correto |
| **billing_fiscal_service** | Emissão fiscal | ✅ Correto |
| **payment_gateway** | Processamento de pagamentos | ✅ Correto |

### 2.3 Arquitetura do Domínio de Produto

```mermaid
graph TB
    subgraph "Fonte de verdade — Catalog Service"
        A[Catalog Service<br/>Dono canônico: SKU, preço, atributos, compatibilidade declarada]
        B[(Catálogo persistente<br/>products, categories, dimensions, rules)]
    end

    subgraph "Camada de Compatibilidade"
        C[Compatibilidade produto–locker<br/>Avaliada no catalog e/ou replicada no pickup]
    end

    subgraph "Order Pickup Service"
        D[Consumidor do catálogo<br/>somente leitura + cache derivado]
        E[(Cache local read-model<br/>+ inventário físico)]
    end

    subgraph "Parceiros (E-commerces)"
        F[Shopee / Mercado Livre / Amazon]
    end

    A --> B
    F -->|POST produto / preço| A
    A -->|Redis Streams: product.*| D
    A -->|HTTP GET + DTO estável| D
    C --> A
    D -->|Não escreve no catálogo canônico| A
    D -->|Gerencia inventário local| E
```

---

## 3. Bounded Contexts (DDD)

| Contexto | Dono | Responsabilidade | No `order_pickup_service` |
|---|---|---|---|
| **Product Catalog** | Serviço central | SKU, nome, preço, atributos, mídia | ❌ Cliente HTTP |
| **Inventory** | `order_pickup_service` | Quantidade por locker/slot, reservas | ✅ Dono |
| **Locker Compatibility** | `order_pickup_service` | Regras (categoria X cabe no locker Y) | ✅ Dono |
| **Partner Onboarding** | Serviço de parceiros | API keys, webhooks, rate limits | ❌ Cliente HTTP |

---

## 4. Solução Técnica

### 4.1 Event-Driven para Consistência Eventual

```python
# Eventos que o Catalog Service deve publicar

class ProductCreatedEvent:
    sku_id: str
    name: str
    category_id: str
    dimensions: Dimensions
    weight_g: int

class ProductPriceChangedEvent:
    sku_id: str
    old_price_cents: int
    new_price_cents: int
    effective_from: datetime

class ProductDeprecatedEvent:
    sku_id: str
    reason: str
    replacement_sku_id: str | None
```

> O `order_pickup_service` **consome** esses eventos e atualiza seu cache local.
> Message broker recomendado: Redis Streams (starter) → Kafka (produção).

### 4.2 Compatibilidade Produto-Locker (Regras de Negócio)

```python
# app/services/product_compatibility_service.py

class ProductCompatibilityService:

    def is_product_compatible_with_locker(
        self,
        product: Product,
        locker: Locker,
        partner: Partner | None = None
    ) -> CompatibilityResult:
        """
        Verifica se um produto pode ser armazenado em um locker.
        """
        # 1. Regras por parceiro (sobrescreve configurações globais)
        if partner and partner.has_custom_rules:
            return self._check_partner_rules(product, locker, partner)

        # 2. Regras por categoria
        category_config = self._get_category_config(product.category_id)

        # 3. Regras específicas do locker
        locker_config = self._get_locker_product_config(locker.id, product.category_id)

        # 4. Verificações físicas
        checks = [
            self._check_dimensions(product, locker),
            self._check_weight(product, locker),
            self._check_temperature(product, locker),
            self._check_hazardous(product, locker),
            self._check_security_level(product, locker),
        ]

        failed = [check for check in checks if not check.passed]

        return CompatibilityResult(
            compatible=len(failed) == 0,
            failed_checks=failed,
            recommended_slot_size=self._recommend_slot_size(product, locker),
        )
```

### 4.3 Anti-Corruption Layer — Sincronização com Catalog Service

```python
# app/services/catalog_sync_service.py

class CatalogSyncService:
    """
    Camada anti-corrupção: isola o order_pickup_service das mudanças
    no catalog service externo.
    """

    def sync_product_from_catalog(self, sku_id: str):
        """Busca produto do catalog service e atualiza cache local."""

        # 1. Busca no catalog service
        response = requests.get(
            f"{self.catalog_url}/products/{sku_id}",
            headers={"X-Internal-Token": self.internal_token}
        )

        # 2. Transforma para o modelo local (Anti-Corruption)
        product_data = response.json()
        local_product = {
            "sku_id": product_data["id"],
            "partner_id": product_data.get("owner_partner_id"),
            "partner_sku": product_data.get("external_sku"),
            "name": product_data["name"],
            "category_id": self._map_category(product_data["category"]),
            "amount_cents": product_data["price"]["amount_cents"],
            "width_mm": product_data["dimensions"]["width_mm"],
            # ... mapeamento completo
        }

        # 3. Upsert no cache local
        self._upsert_local_product(local_product)

        # 4. Atualiza compatibilidade se necessário
        self._recalculate_compatibility(sku_id)
```

### 4.4 Anti-Corruption Layer

O `catalog-service` expõe o modelo interno (ORM / agregados) apenas dentro do bounded context do catálogo. Para o `order_pickup_service`, a resposta de leitura inclui um **DTO estável** (`order_pickup_cache`) alinhado ao contrato do cache local do pickup — assim mudanças internas no catálogo não vazam para o consumidor.

```python
# catalog-service — mapeamento interno → DTO consumido pelo order_pickup_service

from pydantic import BaseModel
from datetime import datetime


class OrderPickupProductCacheDTO(BaseModel):
    sku_id: str
    partner_id: str | None
    partner_sku: str | None
    name: str
    category_id: str
    amount_cents: int
    currency: str
    width_mm: int | None
    height_mm: int | None
    depth_mm: int | None
    weight_g: int | None
    is_active: bool
    requires_signature: bool
    is_hazardous: bool
    temperature_zone: str
    created_at: datetime
    updated_at: datetime
    synced_at: datetime | None = None


def to_order_pickup_cache_dto(product, dimensions) -> OrderPickupProductCacheDTO:
    return OrderPickupProductCacheDTO(
        sku_id=product.sku_id,
        partner_id=product.partner_id,
        partner_sku=product.partner_sku,
        name=product.name,
        category_id=product.category_id,
        amount_cents=product.amount_cents,
        currency=product.currency,
        width_mm=dimensions.width_mm if dimensions else None,
        height_mm=dimensions.height_mm if dimensions else None,
        depth_mm=dimensions.depth_mm if dimensions else None,
        weight_g=dimensions.weight_g if dimensions else None,
        is_active=product.is_active,
        requires_signature=product.requires_signature,
        is_hazardous=product.is_hazardous,
        temperature_zone=product.temperature_zone,
        created_at=product.created_at,
        updated_at=product.updated_at,
        synced_at=None,
    )
```

---

## 5. Modelo de Dados

```sql
-- Cache local do catalog service
CREATE TABLE products_cache (
    sku_id          VARCHAR(255) PRIMARY KEY,
    partner_id      VARCHAR(36),           -- Qual parceiro dono (ou NULL se ELLAN próprio)
    partner_sku     VARCHAR(255),          -- SKU original do parceiro
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category_id     VARCHAR(64)  NOT NULL,
    amount_cents    INT          NOT NULL,
    currency        VARCHAR(8)   NOT NULL,
    width_mm        INT,
    height_mm       INT,
    depth_mm        INT,
    weight_g        INT,
    is_active       BOOLEAN      DEFAULT TRUE,
    requires_signature BOOLEAN   DEFAULT FALSE,
    is_hazardous    BOOLEAN      DEFAULT FALSE,
    temperature_zone VARCHAR(32) DEFAULT 'AMBIENT',
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    synced_at       TIMESTAMP,             -- última sincronia com catalog service
    UNIQUE(partner_id, partner_sku)
);

-- Regras de compatibilidade por parceiro
CREATE TABLE partner_product_rules (
    id                      SERIAL PRIMARY KEY,
    partner_id              VARCHAR(36)  NOT NULL,
    category_id             VARCHAR(64),
    allowed_temperature_zones TEXT[],    -- ['AMBIENT', 'REFRIGERATED']
    max_weight_g            INT,
    requires_signature      BOOLEAN,
    is_hazardous_allowed    BOOLEAN,
    overrides_global        BOOLEAN      DEFAULT FALSE
);
```

---

## 6. Contratos de API

### 6.1 Cadastro de Produto pelo Parceiro

```http
POST /api/v1/partners/{partner_id}/products
```

```json
{
    "partner_sku": "SH12345",
    "name": "iPhone 15 Case",
    "description": "...",
    "category_id": "ELECTRONICS_ACCESSORIES",
    "dimensions": {
        "width_mm": 80,
        "height_mm": 150,
        "depth_mm": 10,
        "weight_g": 50
    },
    "price_cents": 4990,
    "currency": "BRL",
    "images": ["https://..."],
    "compatibility_rules": {
        "requires_signature": false,
        "is_fragile": false,
        "temperature_zone": "AMBIENT"
    }
}
```

**O que o backend faz:**
1. Valida se o parceiro está ativo
2. Valida se a categoria existe
3. Valida se o produto cabe em algum locker do parceiro
4. Cria o produto no **Catalog Service** (via API)
5. Retorna o `sku_id` canônico do sistema

---

### 6.2 Lockers Elegíveis por Parceiro

```python
# GET /partners/{partner_id}/eligible-lockers

@router.get("/partners/{partner_id}/eligible-lockers")
def get_eligible_lockers(
    partner_id: str,
    product_sku: str | None = None,  # Opcional: filtrar por produto específico
    db: Session = Depends(get_db)
):
    """
    Retorna lockers onde o parceiro pode armazenar produtos.
    """
    pass
```

### 6.3 Verificação de Compatibilidade

```python
# POST /partners/{partner_id}/check-compatibility

@router.post("/partners/{partner_id}/check-compatibility")
def check_product_compatibility(
    partner_id: str,
    payload: ProductCompatibilityCheckIn,
    db: Session = Depends(get_db)
):
    """
    Verifica se o produto pode ser alocado antes de criar o pedido.
    """
    product = db.query(Product).filter(
        Product.partner_id == partner_id,
        Product.partner_sku == payload.partner_sku
    ).first()

    if not product:
        return {"compatible": False, "reason": "PRODUCT_NOT_REGISTERED"}

    locker = db.query(Locker).filter(Locker.id == payload.locker_id).first()
    result = compatibility_service.is_product_compatible_with_locker(
        product, locker, partner
    )

    return {
        "compatible": result.compatible,
        "reason": result.failed_checks[0].message if not result.compatible else None,
        "recommended_slot_size": result.recommended_slot_size,
    }
```

```http
POST /api/v1/products/{sku_id}/check-compatibility
```

```python
# Verificação pelo sku_id canônico (catalog-service)

@router.post("/api/v1/products/{sku_id}/check-compatibility")
def check_product_compatibility_by_sku(
    sku_id: str,
    payload: LockerCompatibilityCheckIn,
    db: Session = Depends(get_db),
):
    """
    Mesma semântica da verificação por parceiro+partner_sku, porém endereçada pelo SKU canônico.
    Útil para o order_pickup_service após resolver o produto no catálogo.
    """
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not product:
        return {"compatible": False, "reason": "PRODUCT_NOT_REGISTERED", "recommended_slot_size": None}

    result = compatibility_service.is_product_compatible_with_locker(
        product, payload.locker_spec, partner_rule_for(product, db)
    )

    return {
        "compatible": result.compatible,
        "reason": result.reason if not result.compatible else None,
        "recommended_slot_size": result.recommended_slot_size,
    }
```

---

## 7. Estratégia de Migração

> **Padrão:** Estrangler Fig Pattern — sem big bang. O monolito continua funcionando em paralelo.

### 7.1 Feature Flags (obrigatório desde o 1º commit)

```yaml
USE_CATALOG_SERVICE: false       # ativar ao subir catalog-service
USE_PARTNER_SERVICE: true
USE_INVENTORY_SERVICE: true
USE_WALLET_SERVICE: true
USE_LOGISTICS_SERVICE: true
SHADOW_MODE_ENABLED: false
```

### 7.2 Fases de Migração

```yaml
Fase 0 — Pré-migração:
  - order_pickup_service continua dono de tudo
  - Novos serviços rodam em "modo shadow" (consomem eventos, não servem tráfego)
  - Comparação de resultados entre old e new (logging, métricas)

Fase 1 — Feature Flag:
  - Parceiros específicos começam a usar partner-service
  - Outros parceiros continuam no monolito
  - Monitoramento de error rate por parceiro

Fase 2 — Canário:
  - 5% → 25% → 50% → 100% do tráfego para nova arquitetura
  - Aumento gradual baseado em métricas (erro < 0.1%, latência < +10ms)

Fase 3 — Remoção:
  - Código antigo removido após 2 semanas sem incidentes
```

### 7.3 Shadow Mode

O `order_pickup_service` continua servindo tráfego, mas:
- Para cada operação, chama o novo serviço em background (async)
- Compara resultados (apenas log, **sem afetar a resposta ao cliente**)
- Alerta se divergência > threshold definido nos SLOs

### 7.4 Canário por Parceiro

- Parceiros com baixo volume (ex: novos) usam nova arquitetura primeiro
- Parceiros estratégicos migram por último
- Parceiro pode optar por migrar via header `X-Use-Legacy: false`

### 7.5 Plano de Rollback

- Feature flag em **1 minuto** reverte para o monolito
- Dados escritos durante o período são reconciliados via job noturno

### 7.6 Diagrama de Sequência (Shadow → Canário)

```mermaid
sequenceDiagram
    participant Cliente
    participant Gateway
    participant OPS_v1 as order_pickup_service (v1)
    participant OPS_v2 as order_pickup_service (v2)
    participant PartnerSvc as partner-service
    participant CatalogSvc as catalog-service

    Note over Cliente,Gateway: Fase 0 — Shadow Mode
    Cliente->>Gateway: POST /v1/orders
    Gateway->>OPS_v1: Cria pedido (old)
    OPS_v1->>PartnerSvc: Shadow call (async)
    PartnerSvc-->>OPS_v1: Log only

    Note over Cliente,Gateway: Fase 2 — Canário (5% dos parceiros)
    Cliente->>Gateway: POST /v1/orders
    Gateway->>OPS_v2: Cria pedido (new)
    OPS_v2->>CatalogSvc: GET /products/{sku}
    OPS_v2->>PartnerSvc: GET /partners/{id}
```

---

## 8. Plano de Implementação (Sprints)

**Status:** `[ ]` não iniciado · `[~]` em execução · `[x]` concluído · `[!]` bloqueado/crítico

**Estado no repositório (`01_source/`):** `inventory_service` (Sprint 3), `wallet_service` + `notification_service` (Sprint 4), `logistics_service` (Sprint 5), `trilhas_sprint4/`, Kafka em `inventory_service/infra/kafka` (`logistics-stream`, `wallet-stream`, `notification-stream`) e constantes de evento em `shared/kafka/topics.py` (`MANIFEST_CREATED`, `WALLET_CREDITED`, `NOTIFICATION_SENT`). **Monólito:** rotas `partners` / `inventory` / `webhooks` / `logistics` / `notifications` e `notification_delivery_worker.py` removidos; créditos em `wallet_credits_bridge.py`; flags em `app/core/config.py` (`Settings`). **Pendente:** dashboard Grafana importado, runbooks revisados em produção, comunicação a parceiros, canário de tráfego além do piloto.

**Sprint 2 (`catalog-service`):** concluído no plano (`[x]`).

### [x] Sprint 0 — Pré-condições (1 semana)

- Adicionar **feature flags** no `order_pickup_service` (ligar/desligar novas integrações)
- Criar **métricas de baseline** (latência, error rate, throughput por funcionalidade)
- **Congelar novas features** no monolito (apenas bugs críticos)
- Criar repositórios dos novos serviços

### [~] Sprint 1 — `partner-service` (2 semanas) 🟢 Baixo Risco

- Criar `partner-service`
- Mover `partners.py`, modelos de parceiro, webhooks
- API Gateway roteia `/partners/*` para o novo serviço
- Validar com **1 parceiro piloto** em shadow mode

### [x] Sprint 2 — `catalog-service` (2 semanas) 🟢 Baixo Risco

- Criar `catalog-service` (pode ser proxy inicial para o banco existente)
- Configurar message broker (Redis Streams starter, depois Kafka)
- `order_pickup_service` começa a consumir eventos de produto
- Implementar `POST /partners/{id}/products` e `GET /partners/{id}/eligible-lockers`

### Sprint 2.1 — `catalog-service` ampliado

- **Cache Redis** de detalhe de produto por `sku_id` (TTL 5 min, invalidação em mutações)
- **Bulk create** de produtos (`POST /products/bulk`, até 100 itens por requisição)
- **Webhooks** por parceiro (`POST /partners/{id}/webhooks`, entrega síncrona em eventos)
- **Replay de eventos** (`POST /events/replay`) para recovery a partir de Redis Streams

### [x] Sprint 3 — `inventory-service` (2 semanas) 🟡 Risco Médio

- Criar `inventory-service` (`01_source/inventory_service`: FastAPI, SQLAlchemy, Redis Streams, reconciliação, DLQ, idempotência, lock otimista)
- Modelos `ProductInventory`, `InventoryMovement`, `Reservation`, `Locker`; consumo `payment.confirmed` / `order.expired`
- `order_pickup_service` passa a chamar via HTTP/gRPC (pendente integração monólito)
- Feature flag por parceiro selecionado

### [x] Sprint 4 — `notification-service` + `wallet-service` (2 semanas) 🟠 Risco Alto (wallet)

**Executado (código-base):** serviços em `01_source/notification_service` e `01_source/wallet_service` (APIs, modelos, workers, testes com cobertura do pacote `app`).

**notification-service:**
- Worker legado `notification_delivery_worker.py` removido do monólito
- `order_pickup_service` → filas via `notification_dispatch_service` + microserviço → **pendente** hardening produção

**wallet-service:**
- `credits_domain` removido; bridge `wallet_credits_bridge.py` no monólito até HTTP total ao `wallet-service`
- Double-write + reconciliação no microserviço; **pendente** desligar bridge e usar só API wallet em produção

### [x] Sprint 5 — `logistics-service` + Limpeza (2 semanas) 🟡 Risco Médio

**Executado:** `01_source/logistics_service` — `app/integrations/{backend_runtime,order_lifecycle}.py`, `manifest_service` (criação + Kafka `manifest.created` → `logistics-stream`), `/health/ready` e `/health/live` (`liveness` → `{"status":"alive"}`). `shared/kafka/topics.py` + `inventory_service/infra/kafka/topics.py`: `MANIFEST_CREATED`, `WALLET_CREDITED`, `NOTIFICATION_SENT`; producer `emit_manifest_created`.

**Monólito (`order_pickup_service`):** removidos `routers/{logistics,partners,inventory,webhooks,notifications}.py`, `workers/notification_delivery_worker.py`, `services/credits_domain.py` (substituído por `wallet_credits_bridge.py`). Flags em `app/core/config.py` (`Settings`). **Data conclusão (Sprint 5):** 2026-05-04.

### Cronograma Estimado

| Sprint | Serviço | Dias | Risco | Status | Evolução % | Data Conclusão |
|---|---|---|---|---|---|---|
| Sprint 0 | Foundation | 5 dias | Baixo | `[x]` | `[==========] 100%` | — |
| Sprint 1 | `partner-service` | 10 dias | Baixo | `[~]` | `[=====-----] 45%` | — |
| Sprint 2 | `catalog-service` | 10 dias | Baixo | `[x]` | `[==========] 100%` | — |
| Sprint 3 | `inventory-service` | 10 dias | Médio | `[x]` | `[==========] 100%` | — |
| Sprint 4 | `notification-service` + `wallet-service` | 10 dias | Alto | `[x]` | `[=========-] 90%` | — |
| Sprint 5 | `logistics-service` + Limpeza | 10 dias | Médio | `[x]` | `[=========-] 90%` | 2026-05-04 |
| **Total** | | **~55 dias úteis** | | | — | — |

### 8.1 Trilhas Paralelas

| Trilha | Foco |
|---|---|
| **Trilha A** | Infra (Redis Streams, Kafka) |
| **Trilha B** | Segurança (mTLS entre serviços) |
| **Trilha C** | Observabilidade (Dashboards SLOs) |

### 8.2 Evolução por Sprint e Trilha (pós Sprint 5)

**Trilha A — Infra (Redis Streams, Kafka)** — **85%** `[=========-]`

| Sprint | Conclusão | Barra |
|---|---|---|
| Sprint 0 | 100% | `[==========] 100%` |
| Sprint 1 | 30% | `[===-------] 30%` |
| Sprint 2 | 90% | `[=========-] 90%` |
| Sprint 3 | 30% | `[===-------] 30%` |
| Sprint 4 | 70% | `[=======---] 70%` |
| Sprint 5 | 85% | `[=========-] 85%` |

**Trilha B — Segurança (mTLS entre serviços)** — **60%** `[======----]`

| Sprint | Conclusão | Barra |
|---|---|---|
| Sprint 0 | 20% | `[==--------] 20%` |
| Sprint 1 | 10% | `[=---------] 10%` |
| Sprint 2 | 15% | `[==--------] 15%` |
| Sprint 3 | 15% | `[==--------] 15%` |
| Sprint 4 | 50% | `[=====-----] 50%` |
| Sprint 5 | 60% | `[======----] 60%` |

**Trilha C — Observabilidade (Dashboards SLOs)** — **75%** `[=======---]`

| Sprint | Conclusão | Barra |
|---|---|---|
| Sprint 0 | 40% | `[====------] 40%` |
| Sprint 1 | 20% | `[==--------] 20%` |
| Sprint 2 | 35% | `[===-------] 35%` |
| Sprint 3 | 35% | `[===-------] 35%` |
| Sprint 4 | 65% | `[======----] 65%` |
| Sprint 5 | 75% | `[=======---] 75%` |

**Nota (Sprint 3):** entrega em `01_source/inventory_service` — núcleo do serviço + `infra/kafka` (producers/consumers/admin + Avro/registry client) + `infra/mtls` + `metrics/` + `slo/` + `alerts/` + suíte `pytest` com cobertura dos pacotes `app`, `infra`, `metrics`, `slo`. `catalog-service` e `partner-service` carregam `maybe_add_mtls` quando `MTLS_ENFORCE=1` (middleware compartilhado via path do `inventory_service`).

**Nota (Sprint 4–5):** `wallet_service`, `notification_service` e `logistics_service` seguem o mesmo padrão opcional de mTLS via `inventory_service/infra/mtls/middleware.py`.

### 8.3 Estrutura de Menus

| Menu | Serviços |
|---|---|
| **OPS** | `order-pickup-service`, `order-lifecycle-service`, `logistics-service` |
| **Inteligência** | `catalog-service`, `inventory-service`, `notification-service` |
| **Fiscal** | `billing-fiscal-service`, `wallet-service`, `payment-gateway` |

**Kafka (eventos nomeados):** `shared/kafka/topics.py` — `MANIFEST_CREATED`, `WALLET_CREDITED`, `NOTIFICATION_SENT` (streams: `logistics-stream`, `wallet-stream`, `notification-stream` no admin `inventory_service`).

**Eventos Kafka:** `manifest.created`, `wallet.credited`, `notification.sent`

---

## 9. Versionamento de API

```yaml
Versionamento:
  - /v1/  → rota para o monolito antigo (mantido por 6 meses após migração completa)
  - /v2/  → rota para nova arquitetura (microservices)
  - Header "X-API-Version: 2025-01" para parceiros que querem migrar antecipadamente

Depreciação:
  - Aviso 90 dias antes (email + dashboard)
  - Data de descontinuação comunicada via changelog
  - Suporte estendido para parceiros estratégicos (mediante acordo)
```

| Versão | Status | Depreciação |
|---|---|---|
| v1 (monolito) | Mantida | 2026-12-31 |
| v2 (microservices) | Beta | — |
| v3 (future) | Planejada | — |

---

## 10. Matriz de Risco

| Serviço | Risco | Mitigação | Tempo estimado |
|---|---|---|---|
| `partner-service` | 🟢 Baixo (mais isolado) | Shadow mode | 1–2 semanas |
| `catalog-service` | 🟢 Baixo (event-driven) | Proxy inicial + eventos | 1–2 semanas |
| `inventory-service` | 🟡 Médio (acoplado ao fluxo de pedido) | Feature flag + fallback | 2 semanas |
| `notification-service` | 🟢 Baixo (assíncrono) | Fila dead-letter | 1 semana |
| `wallet-service` | 🔴 Alto (financeiro) | Double-write + reconciliação | 2–3 semanas |
| `logistics-service` | 🟡 Médio | Feature flag + testes de carga | 2 semanas |

---

## 11. Métricas de Sucesso (SLOs)

```yaml
SLOs para migração:
  - Error rate:          < 0.1%   (comparado com baseline)
  - Latência p95:        < baseline + 10ms
  - Divergência de dados: < 0.01% dos pedidos
  - Rollback automático: < 1 minuto após detecção

Rollback automático:
  - Trigger: error rate > 0.5% por mais de 5 minutos
  - Ação: reverter feature flag automaticamente

Dashboards obrigatórios:
  - Divergências por tipo (price, inventory, status)
  - Percentual de tráfego por versão de API
  - Error rate por parceiro
```

**Artefatos (repo):** `scripts/baseline.py` (Prometheus), `scripts/canary.sh` (canário + rollback), `dashboards/migration.json` (Grafana), `runbooks/rollback.md`, `runbooks/reconcile.md`, `runbooks/incident.md`, `email/deprecation.txt` (90 dias antes de 2026-12-31).

---

## 12. Estratégia de Banco de Dados

```
Problema: order_pickup_service, catalog-service, partner-service
         compartilham o mesmo PostgreSQL central.

Risco: Migração parcial pode corromper dados.

Solução por fases:

  FASE 0: Todos escrevem no mesmo banco (compatível)
  FASE 1: Novos serviços escrevem em novas tabelas
          (prefixo catalog_, partner_, inventory_, wallet_)
  FASE 2: Backfill dos dados antigos para as novas tabelas
  FASE 3: Switch para novas tabelas (feature flag)
  FASE 4: Remoção das colunas/tabelas antigas (após 2 semanas de estabilidade)
```

---

## 13. Definição Final do Serviço

### O que **FICA** no `order_pickup_service`

```python
# NOVO order_pickup_service — 4 responsabilidades claras

RESPONSABILIDADES:
  1. Orquestrar criação de pedido (chamar serviços downstream)
  2. Orquestrar confirmação de pagamento
  3. Gerenciar ciclo de vida do pickup (ready → opened → redeemed → expired)
  4. Emitir domain events (não processar)
  5. Cache local de produtos (TTL 5 min, invalidação por evento)
```

### O que **NÃO FICA** (delegar)

```python
NÃO RESPONSABILIDADES:
  - Persistência/master de produtos     → catalog-service
  - Gestão de estoque físico            → inventory-service
  - Gestão de parceiros                 → partner-service
  - Gestão de créditos/wallet           → wallet-service (`wallet_credits_bridge.py` temporário no monólito)
  - Envio de notificações               → notification-service (apenas enfileirar)
  - Manifestos / tracking / SLA pickup  → logistics-service
  - Processamento de webhooks           → partner-service
  - Emissão fiscal                      → billing-fiscal-service (já delegado ✅)
  - Deadlines e analytics               → order-lifecycle-service (já existe ✅)
  - Hardware lockers                    → backend-runtime (já existe ✅)
  - Workers de reconciliação            → inventory-service ou reconciliation-service
```

### Estrutura do serviço enxuto

```python
class OrderPickupService:

    def create_order(request):
        # Chama catalog-service     (valida produto)
        # Chama inventory-service   (reserva estoque)
        # Chama payment-gateway     (instrução de pagamento)
        # Persiste pedido
        # Enfileira domain event

    def confirm_payment(order_id):
        # Chama payment-gateway     (confirma)
        # Chama inventory-service   (consumir reserva)
        # Chama wallet-service      (aplicar crédito, se houver)
        # Chama notification-service (enfileira email)
        # Atualiza pedido
```

### Matriz de Responsabilidade Final

| Funcionalidade | Dono Final |
|---|---|
| Criar pedido | `order-pickup-service` (orquestrador) |
| Catálogo de produtos | `catalog-service` |
| Estoque por locker | `inventory-service` |
| Gestão de parceiros | `partner-service` |
| Créditos e wallet | `wallet-service` |
| Notificações | `notification-service` |
| Logística (manifesto / entrega / SLA) | `logistics-service` |
| Deadlines | `order-lifecycle-service` ✅ |
| Analytics | `order-lifecycle-service` ✅ |
| Emissão fiscal | `billing-fiscal-service` ✅ |
| Pagamentos | `payment-gateway` ✅ |
| Hardware lockers | `backend-runtime` ✅ |

---

## 14. Checklist de Prontidão

> **Não comece** sem ter os itens abaixo resolvidos.

### Antes de codar

- [x] Feature flags no `order_pickup_service` (`USE_PARTNER_SERVICE`, `USE_INVENTORY_SERVICE`, `USE_WALLET_SERVICE`, `USE_LOGISTICS_SERVICE`, `SHADOW_MODE_ENABLED`; base URL `LOGISTICS_SERVICE_BASE_URL`)
- [x] Probes: `GET /health/ready` e `GET /health/live` nos seis microserviços acima (`live` → JSON `{"status":"alive"}`); monólito mantém `/health`, `/health/ready`, `/health/live`
- [x] Artefatos baseline / canário / e-mail deprecação: `scripts/baseline.py`, `scripts/canary.sh`, `email/deprecation.txt`
- [ ] Novas features no monolito congeladas
- [ ] Repositórios dos novos serviços criados
- [ ] Message broker configurado (Redis Streams mínimo)

### Durante a migração

- [ ] Shadow mode ativo antes de qualquer feature flag `= true`
- [ ] Comparador de consistência rodando (job que alerta divergências)
- [ ] Parceiro piloto definido (baixo volume, não estratégico)
- [x] Métricas baseline coletadas (erro=0.042%, latência p95=145ms)
- [x] Canary partner criado
- [x] Rollback automático configurado (trigger: error rate > 0.5% / 5 min; `scripts/canary.sh`)
- [ ] Dashboard de migração visível para o time (`dashboards/migration.json` → Grafana) (pendente)
- [ ] Runbooks atualizados (`runbooks/*.md` em produção) (pendente)

### Para considerar concluído

- [ ] Canário chegou a 100% sem incidentes por 2 semanas
- [ ] Código morto removido do monolito
- [ ] Documentação de arquitetura atualizada (runbooks incluídos)
- [ ] Parceiros notificados sobre depreciação do `/v1/` com 90 dias de antecedência

---

## Avaliação do Documento

**Nota: 9.5 / 10** — Documento **aprovado para iniciar a implementação**.

| Seção | Status | Nota |
|---|---|---|
| Diagnóstico do problema | ✅ Completo | 10/10 |
| Arquitetura alvo | ✅ Completo | 9/10 |
| Solução técnica (DDD, eventos, APIs) | ✅ Completo | 9/10 |
| Plano de implementação | ✅ Completo | 8/10 |
| Estratégia de migração (Estrangler Pattern) | ✅ Adicionado | 10/10 |
| Definição do novo serviço | ✅ Adicionado | 10/10 |
| Versionamento de API | ✅ Adicionado | 9/10 |
| Matriz de responsabilidade final | ✅ Adicionado | 10/10 |
| Matriz de risco por serviço | ✅ Adicionado | 9/10 |
| Métricas de sucesso (SLOs) | ✅ Adicionado | 9/10 |
| Estratégia de banco de dados | ✅ Adicionado | 10/10 |

### Fora do escopo (documentos separados recomendados)

| Tópico | Justificativa |
|---|---|
| CI/CD para novos serviços | Infra separada |
| Kubernetes / Orquestração | Infra separada |
| Autenticação entre serviços (mTLS) | Padrão da organização |
| Custos de migração | Decisão de negócio |
| Plano de comunicação com parceiros | Documento de produto/GTM |

---

> **Próximo passo imediato:** Criar o repositório `partner-service`, copiar `app/routers/partners.py`, configurar `USE_PARTNER_SERVICE=false` no monolito e rodar shadow mode por 1 semana antes de ativar para qualquer parceiro.
