# Ecossistema mundial de players locker / PUDO / marketplace

## Objetivo

Modelar **quem** opera no mercado, **como** integrar (capacidades API) e **onde** atua (país/região), com relações entre agregadores, carriers e marketplaces — alinhado ao catálogo `marketplace_channel_partners` e ao domínio ML.

## Camadas

| Camada | Tabela / fonte | Uso |
|--------|----------------|-----|
| Canônico comercial | `marketplace_channel_partners` + `marketplace_channel_capabilities` | Marketplace OPS, sellers, canais |
| ML / scoring | `ml_locker_network_players` | Telemetria, drift, benchmarks por rede |
| Capacidades | `ml_integration_capability_catalog` + `ml_player_capabilities` | Roadmap de integração (REST, webhook, OAuth…) |
| Relações | `ml_player_relations` | Agregador → carrier, marketplace → rede locker |
| Mercados | `ml_market_presence` | Presença por país, densidade, nível de serviço |

## Players adicionais (além dos citados inicialmente)

- **Redes locker / hardware:** SwipBox, Cleveron, Pickup (PL), Quadient, Bloq.it, Packeta, Vinted Go
- **Carriers globais:** USPS, Royal Mail, La Poste, Colissimo, Hermes DE, Yodel, Swiss Post, Australia Post, Blue Dart
- **Hubs / agregadores:** Cainiao, Parcel2Go, EasyPost, Shippo, Intelipost (já no catálogo)
- **Marketplaces:** Amazon US, Walmart, Rakuten, Cdiscount, OTTO, Flipkart
- **Integração recomendada:** sempre via `capabilities` (LOCKER_INVENTORY, LABEL_API, TRACKING_PUSH, ORDERS_WEBHOOK, SELLER_OAUTH, TELEMETRY_STREAM)

## Tipos de relação (`ml_player_relations`)

- `AGGREGATES` — plataforma logística expõe vários carriers (ex.: Melhor Envio → Correios)
- `USES_LOCKER_NETWORK` — marketplace usa rede de terceiros
- `USES_CARRIER` — marketplace depende de carrier nacional
- `OPERATES_WITH` — operação híbrida (ex.: Vinted + Mondial Relay)
- `PARTNER_NETWORK` — parceria entre carriers/redes

## API ML Admin

- `POST /ml-locker-network-players/seed-from-catalog` — sincroniza players + ecossistema
- `GET /ml-player-capabilities`, `/ml-player-relations`, `/ml-market-presence`
- `GET /ml-ecosystem/summary`

## Próximos passos (prod)

1. Aplicar `migrations/004_ml_player_ecosystem.sql` no Postgres central
2. Webhooks reais por capability (não só seed)
3. Vincular `locker_id` / `tenant_id` em features ML à `network_player_code`
4. Score `INTEGRATION_READINESS` = f(capabilities production_ready, market_presence)
