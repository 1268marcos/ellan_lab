# OPS — Fiscal Admin

## Backend (`fiscal_admin_service`)

| Caminho | Papel |
|--------|--------|
| `app/main.py` | FastAPI, prefixo `/api/v1/fiscal-admin` |
| `app/routers/fiscal_issuer_partners.py` | CRUD emissores + webhook + API key |
| `app/routers/fiscal_documents.py` | CRUD `fiscal_documents` |
| `app/routers/fiscal_ops.py` | gaps, health, tenant/product config, approvals, callbacks |
| `migrations/001_fiscal_admin.sql` | DDL core + emissores admin |
| `migrations/002_fiscal_global_ops.sql` | Jurisdições, corredores, certs, readiness, SLA, DLQ, regras NCM |
| `app/data/fiscal_global_seed.py` | Catálogo mundial (BR, PT, ES, DE, US, GB, IN) |
| `app/routers/fiscal_global_ops.py` | Global OPS API |
| `tests/` | pytest (sqlite in-memory) |

### Tabelas Global OPS (novas)

- `fiscal_jurisdictions`, `fiscal_document_type_catalog`
- `fiscal_tax_corridors`, `fiscal_corridor_tax_rules`
- `fiscal_issuer_jurisdiction_grants`, `fiscal_compliance_certifications`
- `fiscal_emission_slo_policies`, `fiscal_integration_readiness`
- `fiscal_webhook_delivery_log`, `fiscal_auto_classification_rules`

### Subir API

```bash
cd 01_source/fiscal_admin_service
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8024 --reload
```

### Testes

```bash
cd 01_source/fiscal_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend v1 (`01_source/frontend`)

- http://localhost:5173/v1/ops/fiscal/admin
- Menu **Fiscal OPS**
- Proxy `/api/fiscal-admin` → `:8024`

## Frontend v0 (`01_source/frontend_v0`)

- http://localhost:5174/v0/ops/fiscal/admin
- Abas: global, emissores, documentos, gaps, corredores, readiness, certificações, NCM/CFOP, SLA, webhook DLQ, config, governança
- Grupo **Fiscal OPS** no menu OPS (12 entradas)
- Proxy `/api/fca` → `:8024`

### Postgres central

```bash
bash 02_docker/postgres_central/ops/apply_fiscal_admin_migrations.sh
```

Referência schema: `02_docker/complete_schema_20260523_d.sql`
