# NOC/SIMT MVP Runbook

Owner: BE  
Contato emergencia: BE + QA no canal do sprint MVP  
Servico: `01_source/backend/runtime`

## Contrato MVP

Base path: `/api/v1/noc`

Endpoints:

- `GET /api/v1/noc/health`
  - Retorno esperado: `{"status":"ok","service":"noc-simt",...}`
- `GET /api/v1/noc/simt/summary`
  - Retorno esperado: resumo de lockers e incidentes em modo `mvp-polling`.
- `POST /api/v1/noc/incidents/ack`
  - Payload:
    ```json
    {
      "incident_id": "INC-MVP-001",
      "acknowledged_by": "noc_operator"
    }
    ```
  - Retorno esperado: `status=acknowledged`.

## Como testar

Com runtime local ativo:

```bash
bash 07_tests/smoke_noc_simt_mvp.sh
```

Ou manualmente:

```bash
curl -fsS http://localhost:8200/api/v1/noc/health
curl -fsS http://localhost:8200/api/v1/noc/simt/summary
curl -fsS -X POST http://localhost:8200/api/v1/noc/incidents/ack \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"INC-MVP-001","acknowledged_by":"noc_operator"}'
curl -fsS http://localhost:8010/api/v1/noc/dashboard
```

## Como reverter

1. Remover `app.include_router(noc_router)` de `01_source/backend/runtime/app/main.py`.
2. Manter `/ops/health` apontando para dashboards legados.
3. Rebuildar/reiniciar o runtime.

## Evidencia de setup

```bash
python -m compileall 01_source/backend/runtime/app
```

## Checklist de Aceite MVP

Smoke command:

```bash
bash 07_tests/smoke_noc_simt_mvp.sh
```

E2E command:

```bash
bash 07_tests/e2e_noc_simt_mvp.sh
```

Rollback:

1. Remover `from app.routers.noc import router as noc_router` de `01_source/backend/runtime/app/main.py`.
2. Remover `app.include_router(noc_router)` de `01_source/backend/runtime/app/main.py`.
3. Se necessario, remover `from app.routers.noc import router as noc_router` e `app.include_router(noc_router)` de `01_source/backend/order_lifecycle_service/app/main.py`.
4. Reiniciar `backend_runtime` e `order_lifecycle_service`; validar `/health` nas portas `8200` e `8010`.

Owners:

- Primario: @be
- Apoio: @fe
- Validacao: @qa
