# OPS — Parceiros & user_roles

## Backend (`partner_admin_service`)

| Caminho | Papel |
|--------|--------|
| `01_source/partner_admin_service/app/main.py` | FastAPI, prefixo `/api/v1/partner-admin` |
| `app/routers/ecommerce_partners.py` | CRUD `ecommerce_partners` |
| `app/routers/logistics_partners.py` | CRUD `logistics_partners` |
| `app/routers/user_roles.py` | CRUD + `POST .../revoke` em `user_roles` |
| `app/routers/users.py` | `GET /users` (lista para concessão de roles) |
| `app/routers/partner_integrations.py` | webhook, API key, contacts |
| `app/services/seed_data.py` | Seed usuários OPS + parceiros demo |
| `migrations/001_partner_admin.sql` | DDL Postgres alinhado ao schema |
| `tests/` | pytest (sqlite in-memory) |

### Subir API

```bash
cd 01_source/partner_admin_service
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8016 --reload
```

### Testes

```bash
cd 01_source/partner_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend (`01_source/frontend`)

| Caminho | Papel |
|--------|--------|
| `src/pages/ops/OpsPartnersAdmin.tsx` | Parceiros e-commerce/logística, webhook, API key |
| `src/pages/ops/OpsUserRoles.tsx` | Gerenciar `user_roles` |
| `src/api/partnerAdmin.ts` | Cliente HTTP |
| `src/router/index.tsx` | Rotas `/ops/partners/admin`, `/ops/access/user-roles` |
| `src/layouts/Menu.tsx` | Grupo **Acesso & Parceiros** |
| `vite.config.ts` | Proxy `/api/partner-admin` → `:8016` |

```bash
# API
cd 01_source/partner_admin_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8016 --reload

# UI
cd 01_source/frontend && npm run dev
```

URLs: **http://localhost:5173/ops/partners/admin** · **http://localhost:5173/ops/access/user-roles** (perfil `ops` ou `admin`).

## Frontend v0 (porta 5174)

| Caminho | Papel |
|--------|--------|
| `src/pages/OpsPartnersAdminPage.jsx` | Mesmo contrato que frontend |
| `src/pages/OpsUserRolesPage.jsx` | Papéis `user_roles` |
| `src/App.jsx` | Menu grupo **Acesso** + rotas |
| `vite.config.js` | Proxy `/api/pa` → `:8016` |

```bash
cd 01_source/frontend_v0 && npm run dev
```

URLs: **http://localhost:5174/v0/ops/partners/admin** · **http://localhost:5174/v0/ops/access/user-roles** — role `admin_operacao` para mutações.

Menu v0: dropdown **OPS menu** → grupo **Acesso** (subgrupo **Parceiros**), badge **NEW**. Também em **Lockers**: `ops /lockers/create`.

Referência de dados: `02_docker/complete_schema_20260521_c.sql` (`user_roles`, `ecommerce_partners`, `logistics_partners`, `partner_webhook_endpoints`, `partner_api_keys`).
