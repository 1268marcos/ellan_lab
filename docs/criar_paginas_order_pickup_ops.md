# OPS — Order Pickup Admin

## Backend (`order_pickup_admin_service`)

| Caminho | Papel |
|--------|--------|
| `01_source/order_pickup_admin_service/app/main.py` | FastAPI, prefixo `/api/v1/order-pickup-admin` |
| `app/routers/ecommerce_partners.py` | CRUD `ecommerce_partners` |
| `app/routers/logistics_partners.py` | CRUD `logistics_partners` |
| `app/routers/partner_integrations.py` | webhook, API key |
| `app/routers/orders.py` | CRUD `orders` |
| `app/routers/pickups.py` | list/create/update `pickups` |
| `app/routers/credits.py` | list `credits` |
| `app/routers/integration_outbox.py` | list + replay `partner_order_events_outbox` |
| `app/routers/fulfillment.py` | list `order_fulfillment_tracking` |
| `app/services/seed_data.py` | Seed demo |
| `migrations/001_order_pickup_admin.sql` | DDL Postgres alinhado ao schema |
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
cd 01_source/order_pickup_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend (`01_source/frontend`)

| Caminho | Papel |
|--------|--------|
| `src/pages/ops/OpsOrderPickupAdmin.tsx` | UI admin order pickup |
| `src/api/orderPickupAdmin.ts` | Cliente HTTP |
| `src/router/index.tsx` | Rota `/ops/order-pickup/admin` |
| `src/layouts/Menu.tsx` | Grupo **Cadastros OPS** → Order Pickup |
| `vite.config.ts` | Proxy `/api/order-pickup-admin` → `:8018` |

```bash
cd 01_source/order_pickup_admin_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8018 --reload
cd 01_source/frontend && npm run dev
```

- http://localhost:5173/v1/ops/order-pickup/admin

## Frontend v0 (porta 5174)

| Caminho | Papel |
|--------|--------|
| `src/pages/OpsOrderPickupAdminPage.jsx` | Mesmo contrato |
| `src/App.jsx` | OPS menu → **Cadastros OPS** → subgrupo **Order Pickup** |
| `vite.config.js` | Proxy `/api/opa` → `:8018` |

Menu OPS: **Cadastros OPS** → Tenants | Parceiros | Papéis | Payment Gateway | **Order Pickup**.

- http://localhost:5174/v0/ops/order-pickup/admin

Referência: `02_docker/complete_schema_20260521_c.sql` (`orders`, `pickups`, `credits`, `partner_order_events_outbox`, `order_fulfillment_tracking`, parceiros).
