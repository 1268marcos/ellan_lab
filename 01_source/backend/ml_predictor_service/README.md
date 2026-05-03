# ml_predictor_service

Manutenção preditiva (Fase 1): RandomForest sobre `ml_features_daily`, predição em `ml_predictions_log`, metadados em `ml_model_metadata`. A MV `ml_features_daily_mv` agrega `locker_telemetry`, `door_state` e `locker_slots`.

## Variáveis

| Variável | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://admin:admin@localhost:5432/ellan ERRADO` |
| `DATABASE_URL` | `postgresql://admin:admin123@postgres_central:5432/locker_central` |
| `MODEL_ARTIFACT_PATH` | `./artifacts/rf_failure.joblib` |
| `ENABLE_TRAIN_SCHEDULER` | `false` — se `true`, treino diário às 02:00 (`SCHEDULER_TIMEZONE`, default `America/Sao_Paulo`) |
| `SCHEDULER_HOUR` | `2` |

## Rotas

- `POST /train` — treina com linhas `feature_date < hoje` e últimos 90 dias; atualiza MV (concurrent), grava modelo e `ml_model_metadata`.
- `GET /predict/{locker_id}` — última linha de features do locker; grava predição no log.
- `GET /health` — ficheiro do modelo + DB + modelo ativo.
- `GET /metrics` — último `metrics_json` (accuracy, precision, recall).
- `GET /intelligence/dashboard` — séries e lockers com último `health_score < 30` (UI OPS).

## Cron (alternativa ao scheduler)

`0 2 * * * cd .../ml_predictor_service && .venv/bin/python scripts/train_daily.py`
