# Ecossistema mundial locker — FINANCE

Modelo em camadas para integrar **redes locker**, **operadores de rede**, **carriers**, **marketplaces**, **pontos de coleta**, **agregadores/hubs**, **food delivery** e **cross-border** em nível profissional.

## Camadas de dados

| Camada | Tabela / fonte | Função |
|--------|----------------|--------|
| Catálogo | `finance_locker_network_catalog` | Player canónico (`code`), segmento, capabilities, billing |
| Segmentos | `finance_ecosystem_segments` | Taxonomia (8 base + `CROSS_BORDER_HUB`, `RETAIL_PICKUP`) |
| Relações | `finance_player_relations` | Grafo: `OPERATES_NETWORK`, `WHITE_LABEL`, `AGGREGATES`, `FULFILLS_FOR`, … |
| Capabilities | `finance_player_capabilities` | `LOCKER_INVENTORY`, `LABEL_API`, `ORDERS_WEBHOOK`, … |
| Aliases | `finance_player_aliases` | `MELI` → `MERCADOLIVRE`, `PACKSTATION` → `DHL_PACKSTATION` |
| Cobertura | `finance_player_country_coverage` | Serviços por país (locker, PUDO, marketplace, food) |
| Blueprints | `finance_integration_blueprints` | Padrão de integração por segmento (OAuth, webhooks, mTLS) |
| Tipos relação | `finance_relation_types` | Vocabulário controlado do grafo |

Fonte estática (sync): `app/data/global_locker_finance_catalog*.py`

## Como integrar um player novo

1. Adicionar entrada em `global_locker_finance_catalog.py` ou `_expansion.py` com `_entry(...)`.
2. Definir `PLAYER_RELATIONS` se depender de carrier/rede (ex. marketplace → Correios).
3. Opcional: `PLAYER_ALIASES` para códigos legados da API do parceiro.
4. Opcional: linhas em `COUNTRY_COVERAGE` por mercado.
5. `POST /api/v1/finance-admin/locker-network-catalog/sync`
6. Alinhar corredor fiscal em `fiscal_admin_service` (`fiscal_global_seed.py`) se emitir NF no país.

## Players além dos 10 prioritários (exemplos na expansão)

- **Locker / operador:** Hive Box, Luxer One, Instabox, PostNL Locker, Relais Colis, Collect+
- **Carrier / cross-border:** SF Express, 4PX, Yanwen, Chronopost, Ninja Van, OnTrac
- **Marketplace:** Lazada, Allegro, Bol.com, JD.com, Etsy, Target
- **Retail pickup:** IKEA Click & Collect, Decathlon, Leroy Merlin
- **Agregador:** Sendcloud, ShipEngine, nShift, Olist, Flexport
- **Food:** Just Eat, Grubhub (além de iFood, Uber Eats, Deliveroo, Glovo)

## API OPS

```bash
curl -X POST http://localhost:8123/api/v1/finance-admin/locker-network-catalog/sync
curl http://localhost:8123/api/v1/finance-admin/locker-network-catalog/ecosystem-matrix
curl http://localhost:8123/api/v1/finance-admin/locker-network-catalog/integration-blueprints
curl http://localhost:8123/api/v1/finance-admin/locker-network-catalog/resolve/MELI
curl "http://localhost:8123/api/v1/finance-admin/locker-network-catalog/country-coverage?catalog_code=INPOST"
```

## UI

- **Finance OPS** → aba Redes mundiais: clique num player prioritário ou **Como integrar** na tabela → painel com blueprint, passos, capabilities, relações, cobertura e readiness.
- `finance_catalog_code` unifica lookup: Partners `/ecosystem/players/by-finance-code/{code}` · ML `/ml-locker-network-players/by-finance-code/{code}`.

## Readiness por blueprint

- `POST /partner-readiness/recompute` — score inclui `blueprint_score` (até 20 pts) e `integration_blueprint_code`.
- Job agendado: `POST /jobs/run/READINESS_RECOMPUTE`.
