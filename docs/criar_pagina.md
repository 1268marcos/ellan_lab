# OPS — Criar locker(s)

## Backend (`locker_create_service`)

| Caminho | Papel |
|--------|--------|
| `01_source/locker_create_service/app/main.py` | FastAPI, prefixo `/api/v1/locker-create` |
| `app/routers/lockers.py` | CRUD + `POST /lockers/bulk` |
| `app/routers/webhooks.py` | `PUT/GET /lockers/{id}/webhook` |
| `app/routers/api_keys.py` | `POST /lockers/{id}/api-keys/rotate`, `GET .../api-keys` |
| `app/models/` | `lockers`, `locker_slot_configs`, `product_locker_configs`, `locker_webhook_configs`, `locker_api_keys` |
| `migrations/001_locker_webhook_api_keys.sql` | DDL Postgres (webhook + api keys) |
| `tests/` | pytest (sqlite in-memory) |

### Subir API

```bash
cd 01_source/locker_create_service
cp .env.example .env   # DATABASE_URL=postgresql://...
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8015 --reload
```

### Testes

```bash
cd 01_source/locker_create_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend

| Caminho | Papel |
|--------|--------|
| `01_source/frontend/src/pages/ops/OpsLockerCreate.tsx` | Formulario, bulk JSON, webhook, rotacao de chave |
| `01_source/frontend/src/api/lockerCreate.ts` | Cliente HTTP |
| `01_source/frontend/src/router/index.tsx` | Rota `/ops/lockers/create` (perfil ops/admin) |
| `01_source/frontend/vite.config.ts` | Proxy `/api/locker-create` → `:8015` |

### Usar a pagina

```bash
# terminal 1 — API
cd 01_source/locker_create_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8015 --reload

# terminal 2 — UI
cd 01_source/frontend && npm run dev
```

Abrir: **http://localhost:5173/ops/lockers/create** (login com perfil `ops` ou `admin`).

## Frontend v0 (OPS 64 itens — porta 5174)

| Caminho | Papel |
|--------|--------|
| `01_source/frontend_v0/src/pages/OpsLockerCreatePage.jsx` | Mesmo shell que `product-configs` |
| `01_source/frontend_v0/src/App.jsx` | Menu `ops /lockers/create` + rota |
| `01_source/frontend_v0/vite.config.js` | Proxy `/api/lc` → `:8015` |

```bash
# API locker-create
cd 01_source/locker_create_service && PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8015 --reload

# UI v0
cd 01_source/frontend_v0 && npm run dev
```

URL: **http://localhost:5174/v0/ops/lockers/create** — role `admin_operacao` para criar/alterar.

Referencia de dados: `docs/modelo_dados.txt`.
