# App Campo MVP Runbook

Owner: BE  
Contato emergencia: BE + FE no canal do sprint MVP  
Servico: `01_source/backend/runtime`

## Contrato MVP

Base path: `/api/v1/field`

Endpoints:

- `GET /api/v1/field/health`
  - Retorno esperado: `{"status":"ok","service":"field-app"}`
- `POST /api/v1/field/checklist`
  - Payload:
    ```json
    {
      "locker_id": "SP-ALPHAVILLE-SHOP-LK-001",
      "task": "check_power",
      "status": "completed",
      "timestamp": "2026-05-07T13:45:00Z"
    }
    ```
  - Retorno esperado: `{"status":"accepted","item":{...}}`
- `GET /api/v1/field/locker/{locker_id}/status`
  - Retorno esperado: `status=operational` e `slots_free` numerico.

## Como testar

Com runtime local ativo:

```bash
bash 07_tests/smoke_app_campo_mvp.sh
```

Ou manualmente:

```bash
curl -fsS http://localhost:8200/api/v1/field/health
curl -fsS -X POST http://localhost:8200/api/v1/field/checklist \
  -H "Content-Type: application/json" \
  -d '{"locker_id":"SP-ALPHAVILLE-SHOP-LK-001","task":"check_power","status":"completed"}'
curl -fsS http://localhost:8200/api/v1/field/locker/SP-ALPHAVILLE-SHOP-LK-001/status
```

## Como reverter

1. Remover `app.include_router(field_app_router)` de `01_source/backend/runtime/app/main.py`.
2. Manter o frontend apontando para fallback/manual checklist.
3. Rebuildar/reiniciar o runtime.

## Evidencia de setup

```bash
python -m compileall 01_source/backend/runtime/app
```

## Checklist de Aceite MVP

Smoke command:

```bash
bash 07_tests/smoke_app_campo_mvp.sh
```

E2E command:

```bash
bash 07_tests/e2e_app_campo_mvp.sh
```

Rollback:

1. Remover `from app.routers.field_app import router as field_app_router` de `01_source/backend/runtime/app/main.py`.
2. Remover `app.include_router(field_app_router)` de `01_source/backend/runtime/app/main.py`.
3. Reiniciar `backend_runtime` e validar `curl -fsS http://localhost:8200/health`.

Owners:

- Primario: @be
- Apoio: @fe
- Validacao: @qa
