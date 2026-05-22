# OPS — Order Pickup Admin

## Backend (`order_pickup_admin_service`)

| Caminho | Papel |
|--------|--------|
| `01_source/order_pickup_admin_service/app/main.py` | FastAPI, prefixo `/api/v1/order-pickup-admin` |
| `app/routers/ecommerce_partners.py` | CRUD `ecommerce_partners` |
| `app/routers/logistics_partners.py` | CRUD `logistics_partners` |
| `app/routers/partner_integrations.py` | webhook, API key |
| `app/routers/orders.py` | CRUD `orders` |
| `app/routers/pickups.py` | list/create/get/patch `pickups` |
| `app/routers/credits.py` | list/create `credits` |
| `app/routers/integration_outbox.py` | list + replay `partner_order_events_outbox` |
| `app/routers/fulfillment.py` | list + patch `order_fulfillment_tracking` |
| `app/routers/pickup_lifecycle.py` | `order_items`, `pickup_events`, `pickup_tokens`, `pickup_attempts`, `domain_event_outbox` |
| `app/services/seed_data.py` | Seed demo |
| `migrations/001_order_pickup_admin.sql` | DDL Postgres |
| `tests/` | pytest (sqlite in-memory) |

### Subir API

```bash
cd 01_source/order_pickup_admin_service
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8018 --reload
```

### Testes

```bash
make test-order-pickup-admin
```

## Frontend (`01_source/frontend`)

| Caminho | Papel |
|--------|--------|
| `src/pages/ops/OpsOrderPickupAdmin.tsx` | UI admin (Parceiros, Pedidos, Créditos, Integração) |
| `src/api/orderPickupAdmin.ts` | Cliente HTTP |
| `src/router/index.tsx` | Rota `/ops/order-pickup/admin` |
| `src/layouts/Menu.tsx` | Grupo **Order Pickup OPS** |
| `vite.config.ts` | Proxy `/api/order-pickup-admin` → `:8018` |

- http://localhost:5173/v1/ops/order-pickup/admin

## Frontend v0 (porta 5174)

| Caminho | Papel |
|--------|--------|
| `src/pages/OpsOrderPickupAdminPage.jsx` | Mesmo contrato + UX OPS shell |
| `src/App.jsx` | **Cadastros OPS** → subgrupo **Order Pickup** |
| `vite.config.js` | Proxy `/api/opa` → `:8018` |

- http://localhost:5174/v0/ops/order-pickup/admin

Referência: `02_docker/complete_schema_20260521_c.sql` — `orders`, `pickups`, `credits`, `order_items`, `pickup_events`, `pickup_tokens`, `pickup_attempts`, `partner_order_events_outbox`, `domain_event_outbox`, `order_fulfillment_tracking`, parceiros.
