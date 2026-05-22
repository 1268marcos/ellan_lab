# Partner OPS — ecossistema global de lockers

## Objetivo

O domínio **Partner** (`partner_admin_service`) passa a ter catálogo e vínculos dos mesmos players mundiais já modelados em Marketplace e ML Admin, sem duplicar regras de negócio de seller/canal.

## Tabelas

| Tabela | Uso |
|--------|-----|
| `partner_ecosystem_players` | Catálogo mestre (~47 players via sync do `channel_players_catalog`) |
| `partner_ecosystem_links` | Vínculo `partner_id` (e-commerce ou logística) → player |

## Players prioritários (filtro OPS)

InPost, DHL, DPD, CTT, Correios, Magalu, Mercado Livre, Amazon BR/ES, Worten, El Corte Inglés (+ Mondial Relay, Melhor Envio no catálogo completo).

## API (`/api/v1/partner-admin`)

- `GET /ecosystem/players` — lista; query `priority_only`, `parent_group`, `country`, `supports_lockers`
- `POST /ecosystem/players/sync-catalog` — upsert a partir de `marketplace_admin_service/app/data/channel_players_catalog.py`
- `GET /partners/{id}/ecosystem-links`
- `POST /partners/{id}/ecosystem-links`
- `DELETE /partners/{id}/ecosystem-links/{link_id}`

Visão 360 inclui `ecosystem_links` e `ecosystem_priority_links`.

## Alinhamento com outros serviços

| Serviço | Entidade | Relação |
|---------|----------|---------|
| Marketplace OPS | `marketplace_channel_partners` | Mesmo catálogo fonte (`CHANNEL_PLAYERS_CATALOG`) |
| ML Admin | `ml_locker_network_players` | Telemetria / scoring por rede |
| Order pickup | `locker_operators` | `locker_operator_ref` no player (ex. `OP-INPOST-EU-001`) |

## UI

- v1/v0: aba **Redes mundiais** (`?tab=ecosystem`) em `/ops/partners/admin`
- Seed demo: `partner_demo_001` recebe 10 vínculos agregadores após `/seed`
- **Registros OPS**: cada player prioritário ganha linha em `ecommerce_partners` ou `logistics_partners` (`ec-pri-*` / `lg-pri-*`) + vínculo 1:1 no catálogo
- `POST /ecosystem/players/seed-priority-partners` — recria/atualiza cadastros prioritários sem rodar seed completo

## Camada profissional (capabilities + grafo + mercados)

Ver [GLOBAL_LOCKER_ECOSYSTEM_PARTNER.md](./GLOBAL_LOCKER_ECOSYSTEM_PARTNER.md).

- `partner_integration_capability_catalog` / `partner_player_capabilities`
- `partner_player_relations` / `partner_market_presence`
- `POST /ecosystem/players/seed-professional`

## Migrações

- `004_partner_ecosystem.sql` — players + links  
- `005_partner_ecosystem_professional.sql` — capabilities, relations, presença
