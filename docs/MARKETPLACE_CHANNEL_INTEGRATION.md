# Marketplace — players e modos de integração

Catálogo canônico: `01_source/marketplace_admin_service/app/data/channel_players_catalog.py` (~47 players).

## Camadas no domínio

| Entidade | Papel |
|----------|--------|
| `marketplace_channel_partners` | Player (locker, marketplace, carrier, agregador, pagamentos) |
| `marketplace_channel_capabilities` | O que integrar (ORDERS_WEBHOOK, LABEL_API, LOCKER_INVENTORY, …) |
| `seller_channel_listings` | Seller num canal (loja ML, Amazon, …) |
| `seller_locker_network_links` | Seller numa rede locker (InPost, Correios, …) |
| `locker_operator_ref` | Ponte para `locker_operators` no **order_pickup** |

## `parent_group` (filtro OPS)

- **LOCKER_NETWORK** — InPost, Bloq, Mondial Relay, Packeta, Quadient
- **CARRIER_LAST_MILE** — DHL, DPD, CTT, Correios, SEUR, FedEx, Jadlog, Evri
- **MARKETPLACE** — Magalu, ML, Amazon, Shopee, TikTok Shop, AliExpress
- **SHIPPING_AGGREGATOR** — Melhor Envio, EasyPost, ShipStation
- **PAYMENTS** — Stripe Connect, Adyen Marketplace

## `integration_mode`

| Modo | Quando usar |
|------|-------------|
| `LOCKER_NETWORK_API` | Inventário PUDO + drop-off (InPost, redes locker) |
| `BIDIRECTIONAL` | Pedidos + tracking nos dois sentidos (DHL, ML) |
| `DIRECT_API` | REST do player (Correios, CTT, categorias carrier) |
| `WEBHOOK_INBOUND` | Só eventos do player para nós (alguns marketplaces) |
| `AGGREGATOR` | Um contrato cobre N carriers (Melhor Envio, EasyPost) |
| `OAUTH_MARKETPLACE` | Seller autoriza loja (ML, Amazon SP-API) |

## Capabilities (contrato técnico)

Códigos no seed: `ORDERS_WEBHOOK`, `ORDERS_POLL`, `TRACKING_PUSH`, `LOCKER_INVENTORY`, `SETTLEMENT_FEED`, `SELLER_OAUTH`, `LABEL_API`, `RETURNS_RMA`.

Cada capability tem `protocol` (REST, WEBHOOK, OAUTH2) e `direction` (INBOUND / OUTBOUND).

Helpers no catálogo: `catalog_capability_rows()`, `expected_capability_count()`, `expected_capabilities_for_partner(id)`.

Resposta do seed inclui `capabilities_catalog_expected`, `capabilities_db_enabled`, `capabilities_in_sync` (deve ser `true`).

## API OPS

- `POST /channel-partners/seed-players` — upsert catálogo + **espelho 1:1** de `marketplace_channel_capabilities` (remove linhas que saíram do catálogo Python; atualiza protocol/direction)
- `GET /channel-partners?parent_group=LOCKER_NETWORK`
- `GET /channel-partners/integration-matrix` — agrupado por `parent_group`
- `GET /channel-partners/{id}` — player + capabilities

## Fluxo recomendado para novo player

1. Adicionar entrada em `channel_players_catalog.py` (code único, `locker_ref` se existir no order_pickup).
2. `POST seed-players` ou Seed global do marketplace-admin.
3. Criar `seller_channel_listing` ou `seller_locker_network_link` para o seller demo.
4. No **order_pickup**, alinhar `locker_operators` / seed quando `locker_operator_ref` for usado em produção.

## Players além dos “óbvios” (já no catálogo)

| Grupo | Exemplos |
|-------|----------|
| Locker EU | Bloq, Quadient, Packeta, Mondial Relay |
| Carrier | Correos ES, SEUR, GLS, Chronopost, Royal Mail, La Poste |
| BR logistics | Jadlog, Loggi, Total Express |
| Agregadores | Melhor Envio, EasyPost, ShipStation |
| Global commerce | TikTok Shop, AliExpress, eBay |
| Pagamentos split | Stripe Connect, Adyen Marketplace |
