# OPS — ML Admin

## Backend (`ml_admin_service`)

| Caminho | Papel |
|--------|--------|
| `app/main.py` | FastAPI, prefixo `/api/v1/ml-admin` |
| `app/routers/ml_data_partners.py` | CRUD parceiros ML + webhook + API key |
| `app/routers/ml_model_metadata.py` | CRUD `ml_model_metadata` |
| `app/routers/ml_features.py` | CRUD `ml_features_daily` |
| `app/routers/ml_predictions.py` | CRUD `ml_predictions_log` |
| `app/routers/ml_feedback.py` | Feedback + validate + dashboard |
| `app/routers/ml_ops.py` | Use cases, registry, training, catalog, drift, SLO, alerts, deployments, grants |
| `app/routers/ml_network_players.py` | Redes locker mundiais + perfis ML por rede |
| `app/data/locker_network_players_catalog.py` | Catálogo (sync com `marketplace_admin_service` channel_players) |
| `migrations/001_ml_admin.sql` | Parceiros ML admin |
| `migrations/002_ml_ops_governance.sql` | Plataforma ML Ops (governança) |
| `migrations/003_ml_locker_network_players.sql` | `ml_locker_network_players`, `ml_network_ml_profiles`, `network_player_code` em parceiros |
| `migrations/004_ml_player_ecosystem.sql` | Capacidades, relações, presença de mercado, tiers globais |
| `docs/ML_LOCKER_PLAYER_ECOSYSTEM.md` | Visão ecossistema mundial e tipos de integração |
| `tests/` | pytest (sqlite in-memory) |

### Tabelas schema `ml_*` (Postgres central)

- `ml_features_daily`, `ml_model_metadata`, `ml_predictions_log`, `ml_prediction_feedback`
- Admin: `ml_data_partners`, `ml_partner_webhook_endpoints`, `ml_partner_api_keys`
- Governança: `ml_use_cases`, `ml_model_registry`, `ml_training_runs`, `ml_feature_definitions`, `ml_drift_reports`, `ml_inference_slo`, `ml_alert_rules`, `ml_deployment_events`, `ml_partner_use_case_grants`
- Redes locker: `ml_locker_network_players`, `ml_network_ml_profiles` (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Mondial Relay, etc.)

### Seed redes locker

`POST /api/v1/ml-admin/ml-locker-network-players/seed-from-catalog` — importa do catálogo marketplace (ou fallback embutido), cria perfis ML (`NETWORK_HEALTH_BENCHMARK`) e parceiros `TELEMETRY-*` vinculados por `network_player_code`.

### Subir API

```bash
cd 01_source/ml_admin_service
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8021 --reload
```

### Testes

```bash
cd 01_source/ml_admin_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```

## Frontend v1 (`01_source/frontend`)

- http://localhost:5173/v1/ops/ml/admin
- Abas: overview, partners, **networks**, models, features, predictions, feedback
- Proxy `/api/ml-admin` → `:8021`

## Frontend v0 (`01_source/frontend_v0`)

Abas: overview, use_cases, registry, training, partners, **networks**, models, catalog, features, predictions, drift, governance, deployments, grants, feedback.

- http://localhost:5174/v0/ops/ml/admin
- Proxy `/api/mla` → `:8021`

Referência: `02_docker/complete_schema_20260522_A.sql`
