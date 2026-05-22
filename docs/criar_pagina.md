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
| `app/routers/tenants.py` | CRUD `tenant_fiscal_config`, `custom_domains`, `tenant_partner_links` |
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
| `src/router/index.tsx` | Rotas `/ops/partners/admin`, `/ops/access/user-roles`, `/ops/tenants/admin` |
| `src/pages/ops/OpsTenantsAdmin.tsx` | Tenants, domínios white label, vínculos parceiro |
| `src/api/tenantAdmin.ts` | Cliente HTTP tenants |
| `src/layouts/Menu.tsx` | Grupo **Cadastros OPS** (tenants, parceiros, papéis, payment gateway) |
| `vite.config.ts` | Proxy `/api/partner-admin` → `:8016` |

```bash
# API
cd 01_source/partner_admin_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8016 --reload

# UI
cd 01_source/frontend && npm run dev
```

URLs (note o prefixo **`/v1/`** — o app usa `BrowserRouter basename="/v1"`):

- **http://localhost:5173/v1/ops/partners/admin**
- **http://localhost:5173/v1/ops/access/user-roles**
- **http://localhost:5173/v1/ops/tenants/admin** — tenants, domínios e vínculos com parceiros

Perfil necessário: **`ops`** ou **`admin`** (parceiro comum não vê o menu nem a rota).

Menu lateral (perfil ops/admin): grupo **Cadastros OPS** com quatro entradas (Tenants, Parceiros, Papéis, Payment Gateway).

## Frontend v0 (porta 5174)

| Caminho | Papel |
|--------|--------|
| `src/pages/OpsPartnersAdminPage.jsx` | Mesmo contrato que frontend |
| `src/pages/OpsUserRolesPage.jsx` | Papéis `user_roles` |
| `src/pages/OpsTenantsAdminPage.jsx` | Tenants, domínios, vínculos parceiro |
| `src/App.jsx` | OPS menu → grupo **Cadastros OPS** (subgrupos Tenants, Parceiros, Payment Gateway) |
| `vite.config.js` | Proxy `/api/pa` → `:8016` |

```bash
cd 01_source/frontend_v0 && npm run dev
```

URLs (prefixo **`/v0/`** — `BrowserRouter basename="/v0"`):

- **http://localhost:5174/v0/ops/partners/admin**
- **http://localhost:5174/v0/ops/access/user-roles**
- **http://localhost:5174/v0/ops/tenants/admin**

Login v0: **email/senha** (não é o formulário partner_id/api_key do `01_source/frontend` em `:5173`). Role **`admin_operacao`** para Seed/criar.

Menu v0: dropdown **OPS menu** → **Cadastros OPS** → Tenants | Parceiros | Papéis | Payment Gateway (badge **NEW**).

Referência de dados: `02_docker/complete_schema_20260521_c.sql` (`user_roles`, `ecommerce_partners`, `logistics_partners`, `partner_webhook_endpoints`, `partner_api_keys`).
