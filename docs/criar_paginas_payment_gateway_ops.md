# OPS — Payment Gateway Admin

## Backend (`payment_gateway_admin_service`)

| Caminho | Papel |
|--------|--------|
| `01_source/payment_gateway_admin_service/app/main.py` | FastAPI, prefixo `/api/v1/payment-gateway-admin` |
| `app/routers/payment_method_catalog.py` | CRUD `payment_method_catalog` |
| `app/routers/payment_interface_catalog.py` | CRUD `payment_interface_catalog` |
| `app/routers/payment_method_ui_alias.py` | CRUD `payment_method_ui_alias` |
| `app/routers/locker_payment_methods.py` | CRUD `locker_payment_methods` |
| `app/routers/payment_provider_partners.py` | CRUD PSP + webhook + API key |
| `app/routers/gateway_ops.py` | device registry, idempotency, risk events |
| `app/services/seed_data.py` | Seed demo |
| `migrations/001_payment_gateway_admin.sql` | DDL Postgres |
| `tests/` | pytest (sqlite in-memory) |

### Subir API

```bash
cd 01_source/payment_gateway_admin_service
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload
```

### Testes

```bash
cd 01_source/payment_gateway_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend (`01_source/frontend`)

| Caminho | Papel |
|--------|--------|
| `src/pages/ops/OpsPaymentGatewayAdmin.tsx` | UI admin gateway |
| `src/api/paymentGatewayAdmin.ts` | Cliente HTTP |
| `src/router/index.tsx` | Rota `/ops/payment-gateway/admin` |
| `src/layouts/Menu.tsx` | Grupo **Cadastros OPS** → Payment Gateway (PSP) |
| `vite.config.ts` | Proxy `/api/payment-gateway-admin` → `:8017` |

```bash
cd 01_source/payment_gateway_admin_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8017 --reload
cd 01_source/frontend && npm run dev
```

- http://localhost:5173/v1/ops/payment-gateway/admin

## Frontend v0 (porta 5174)

| Caminho | Papel |
|--------|--------|
| `src/pages/OpsPaymentGatewayAdminPage.jsx` | Mesmo contrato |
| `src/App.jsx` | OPS menu → grupo **Cadastros OPS** → subgrupo **Payment Gateway** |
| `vite.config.js` | Proxy `/api/pga` → `:8017` |

Menu OPS (dropdown): **Cadastros OPS** → Tenants | Parceiros | Papéis | Payment Gateway.

- http://localhost:5174/v0/ops/payment-gateway/admin

Referência: `02_docker/complete_schema_20260521_c.sql` + tabelas `payment_provider_*` (admin PSP).
