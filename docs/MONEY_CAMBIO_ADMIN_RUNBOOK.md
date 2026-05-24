# Money & Câmbio Admin — runbook

## Mapa de portas (admin OPS — não alterar sem atualizar vite)

| Porta | Serviço |
|------:|---------|
| 8017 | payment-gateway-admin |
| 8018 | order-pickup-admin |
| 8019 | marketplace-admin |
| 8021 | ml-admin |
| 8022 | privacy-compliance-admin |
| **8123** | **finance-admin** |
| 8024 | fiscal-admin |
| **8125** | **money-cambio-admin** |

Proxies frontend: v0 `/api/mca` → 8125 · v1 `/api/money-cambio-admin` → 8125

### `Address already in use` na 8125

Causas comuns:

1. **uvicorn local** ainda rodando (`./dev.sh` ou comando manual) — conflita com Docker.
2. **Docker** já subiu o container — não rode uvicorn local na mesma porta.

Antes de `docker compose up`, pare o dev local:

```bash
cd ~/ellan_lab/01_source/money_cambio_admin_service && ./dev.sh stop
# ou: fuser -k 8125/tcp
```

Significa também que o serviço **já pode estar rodando**:

```bash
curl http://localhost:8125/api/v1/money-cambio-admin/health
# {"status":"ok","service":"money-cambio-admin"} → não suba de novo

cd ~/ellan_lab/01_source/money_cambio_admin_service
./dev.sh status    # ou: ./dev.sh restart
```

## Backend (porta 8125)

O serviço fica em **`ellan_lab/01_source/money_cambio_admin_service`** (não dentro de `02_docker`).

**Script recomendado (evita porta duplicada):**

```bash
cd ~/ellan_lab/01_source/money_cambio_admin_service
./dev.sh start    # ou: status | stop | restart | seed
```

**Manual (da raiz do repo `~/ellan_lab`):**

```bash
cd 01_source/money_cambio_admin_service
python3 -m venv .venv   # só na primeira vez
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8125 --reload
```

**Se você estiver em `02_docker`:**

```bash
cd ../01_source/money_cambio_admin_service
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8125 --reload
```

**Via Docker Compose:**

```bash
cd 02_docker
docker compose up -d money_cambio_admin_service
curl -X POST http://localhost:8125/api/v1/money-cambio-admin/seed
```

Seed manual:

```bash
curl -X POST http://localhost:8125/api/v1/money-cambio-admin/seed
```

## Testes

```bash
cd 01_source/money_cambio_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontends

| App | URL | Proxy |
|-----|-----|-------|
| v1 | http://localhost:5173/v1/ops/money-cambio/admin | `/api/money-cambio-admin` → `:8125` |
| v0 | http://localhost:5174/v0/ops/money-cambio/admin | `/api/mca` → `:8125` |

## Tabelas (schema)

**Catálogo base**

- `money_currency_catalog` — moedas ISO
- `payment_method_catalog`, `payment_interface_catalog`, `payment_method_ui_alias`, `wallet_provider_catalog`

**Nível profissional / mundial** (`migrations/002_money_cambio_professional.sql`)

- `money_operating_country` — países, moeda padrão, zona regulatória, redes locker
- `money_method_country_matrix` — disponibilidade método × país (limites, KYC)
- `money_wallet_country_matrix` — wallet × país
- `cambio_payment_corridor` — corredores cross-border (spread bps, moedas)
- `cambio_corridor_markup` — markup por parceiro/corredor
- `money_compliance_limit` — limites AML/KYC por país
- `cambio_fx_rate_audit` — trilha de alteração de taxas

**Players locker** (`migrations/003_money_locker_player_registry.sql`)

- `money_locker_player_registry` — players com ligação Finance/Fiscal/Câmbio

**Ecossistema mundial** (`migrations/004_money_ecosystem_world.sql`)

- `money_ecosystem_segment` — taxonomia (locker, carrier, marketplace, coleta, hub, food, payments)
- `money_player_relation` — relações OPERATES_NETWORK, WHITE_LABEL, AGGREGATES, etc.

**Integração**

- `cambio_fx_rates` — taxas e `POST /fx-rates/convert`
- `money_cambio_integration_partners` — webhook + API key rotation

## Endpoints OPS adicionais

| Área | Rotas |
|------|--------|
| Dashboard | `GET /global-ops/dashboard` |
| Países | `GET/POST /operating-countries`, `PATCH /operating-countries/{cc}` |
| Matriz | `GET/POST /method-country-matrix` |
| Corredores | `GET/POST /payment-corridors`, `POST /payment-corridors/markups` |
| Compliance | `GET/POST /compliance-limits` |
| Auditoria | `GET /fx-rate-audit` |

Menus OPS: **Money OPS** e **Câmbio OPS** (v0) — overview, countries, **players ecossistema**, **segmentos**, **relações**, matrix, corridors, compliance, audit.

### Ecossistema mundial ↔ Finance ↔ Fiscal

Catálogo: `global_locker_money_catalog.py` + `global_locker_money_catalog_world.py` (~88 players, 8 segmentos, 32 relações). Espelha `finance_admin` `global_locker_finance_catalog_world.py`.

| Segmento | Exemplos |
|----------|----------|
| LOCKER_NETWORK | InPost, SwipBox, Bloq.it |
| LOCKER_NETWORK_OPERATOR | DHL Packstation, USPS Lockers |
| CARRIER_LAST_MILE | DHL, Correios, La Poste, UPS |
| MARKETPLACE | Magalu, Shein, Temu, Rakuten |
| COLLECTION_POINT | Ponto Magalu, Worten Stores |
| LOGISTICS_PLATFORM | Cainiao, Melhor Envio, Shippo |
| FOOD_DELIVERY | iFood, Rappi, Uber Eats |
| PAYMENTS_FISCAL | Stripe Connect, Adyen |

Rotas: `GET /locker-players?segment=FOOD_DELIVERY` · `GET /ecosystem-segments` · `GET /player-relations` · `GET /ecosystem-intelligence` · `GET /ecosystem-matrix`.

### Sync automático com Finance Admin

O Money puxa `finance_locker_network_catalog`, segmentos e relações via HTTP (porta **8123**).

| Variável | Default | Descrição |
|----------|---------|-----------|
| `FINANCE_ADMIN_BASE_URL` | `http://localhost:8123/api/v1/finance-admin` | Base da API Finance |
| `FINANCE_ADMIN_SYNC_ENABLED` | `true` | Desliga sync se `false` |
| `FINANCE_ADMIN_SYNC_ON_START` | `false` | Sync após seed no boot (não bloqueia se Finance offline) |
| `FINANCE_ADMIN_SYNC_AFTER_SEED` | `false` | Sync após `POST /seed` |
| `FINANCE_ADMIN_TIMEOUT_SEC` | `15` | Timeout HTTP |

```bash
# Finance deve estar no ar (catálogo populado)
curl -X POST http://localhost:8123/api/v1/finance-admin/locker-network-catalog/sync

# Money ← Finance
curl -X POST "http://localhost:8125/api/v1/money-cambio-admin/sync/finance-admin?trigger_finance_sync=true"
curl http://localhost:8125/api/v1/money-cambio-admin/sync/finance-admin/status
```

UI v0: botão **Sync Finance** na toolbar OPS. Corredores fiscal/câmbio locais são preservados; preenchidos a partir de `global_locker_money_catalog` quando vazios.

**Erro `Not Found` no Sync Finance:** o processo na **8125** está desatualizado (sem rota `/sync/finance-admin`). Rebuild:

```bash
cd ~/ellan_lab/02_docker
docker compose up -d --build money_cambio_admin_service
```

**Erro `finance_admin_unreachable` (Docker):** o Finance roda no **host** (`8123`), não dentro do Compose. No WSL/Linux o compose inclui `extra_hosts: host.docker.internal:host-gateway`. Antes do sync:

```bash
cd ~/ellan_lab/01_source/finance_admin_service
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8123
curl -X POST http://localhost:8123/api/v1/finance-admin/locker-network-catalog/sync
curl -X POST "http://localhost:8125/api/v1/money-cambio-admin/sync/finance-admin?trigger_finance_sync=true"
```

### Money Intelligence (`migrations/005_money_intelligence.sql`)

| Tabela | Função |
|--------|--------|
| `money_player_readiness` | Score 0–100 por player (fiscal, FX, compliance, relações) |
| `money_ecosystem_insight` | Gaps acionáveis (MISSING_FISCAL_LINK, CORRIDOR_NO_FX, …) |
| `money_fx_alert_rule` / `money_fx_alert_event` | Alertas de volatilidade FX (bps) |
| `money_settlement_schedule` | Calendário T+N por player/corredor |

```bash
curl -X POST http://localhost:8125/api/v1/money-cambio-admin/money-intelligence/analyze
curl http://localhost:8125/api/v1/money-cambio-admin/money-intelligence/dashboard
curl http://localhost:8125/api/v1/money-cambio-admin/money-intelligence/insights?severity=HIGH
```

UI v0: abas **Intelligence** e **Settlement** · botão **Analyze** · KPIs no overview.

### Operações avançadas (`migrations/006_money_advanced_ops.sql`)

| Recurso | Rota | Descrição |
|---------|------|-----------|
| Simulador | `POST /pricing/preview` | FX + spread + markup + compliance + T+N |
| Payment rails | `GET/POST /payment-rails` | Métodos habilitados por player×país |
| Tesouraria | `GET /treasury/dashboard` | Exposição por moeda, gaps FX |
| Trava FX | `GET/POST /fx-locks` | Hedge operacional por corredor (TTL horas) |

UI v0: **Simulador**, **Payment rails**, **Tesouraria**, **Travas FX**.

### Players locker ↔ Finance ↔ Fiscal

Tabela `money_locker_player_registry` — catálogo combinado (alinhado a `finance_locker_network_catalog` e `fiscal_global_seed` corridor_code).

| Player | Finance code | Fiscal corridor |
|--------|--------------|-----------------|
| INPOST | INPOST | PL-EU-INPOST-LOCKER |
| DHL | DHL | DE-DHL-PACKSTATION |
| MAGALU | MAGALU | BR-MAGALU-LOCKER |
| MERCADOLIVRE | MERCADOLIVRE | BR-MELI-LOCKER |
| CORREIOS | CORREIOS | BR-BR-LOCKER-NFCE |
| WORTEN | WORTEN | PT-WORTEN-CC |
| EL_CORTE_INGLES | EL_CORTE_INGLES | ES-ECI-COLLECTION |

`GET /locker-players` · `GET /ecosystem-matrix` (links OPS Finance/Fiscal).

Após deploy: `curl -X POST http://localhost:8125/api/v1/money-cambio-admin/seed`
