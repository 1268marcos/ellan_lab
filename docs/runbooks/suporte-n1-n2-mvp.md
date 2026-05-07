# Suporte N1/N2 MVP Runbook

Owner: BE  
Contato emergencia: BE + QA no canal do sprint MVP  
Servico: `01_source/order_pickup_service`

## Contrato MVP

Base path: `/api/v1/support`

Endpoints:

- `GET /api/v1/support/health`
  - Retorno esperado: `{"status":"ok","service":"support-n1-n2"}`
- `GET /api/v1/support/order/{order_id}`
  - Retorno esperado: timeline MVP mock com `status=completed` e `next_action`.
- `GET /api/v1/support/orders/{order_id}/timeline`
  - Retorno esperado: resumo real do pedido, eventos conhecidos e `next_action`.
  - Se o pedido nao existir: `404 ORDER_NOT_FOUND`.

## Como testar

Com `order_pickup_service` local ativo:

```bash
bash 07_tests/smoke_suporte_n1_n2_mvp.sh
```

Ou manualmente:

```bash
curl -fsS http://localhost:8003/api/v1/support/health
curl -fsS http://localhost:8003/api/v1/support/order/ORDER_ID
```

## Como reverter

1. Remover `app.include_router(support_mvp.router)` de `01_source/order_pickup_service/app/main.py`.
2. Suporte volta a usar telas/rotas OPS legadas para consulta manual.
3. Rebuildar/reiniciar `order_pickup_service`.

## Evidencia de setup

```bash
python -m compileall 01_source/order_pickup_service/app
```

## Checklist de Aceite MVP

Smoke command:

```bash
bash 07_tests/smoke_suporte_n1_n2_mvp.sh
```

E2E command:

```bash
bash 07_tests/e2e_suporte_n1_n2_mvp.sh
```

Rollback:

1. Remover `support` e `support_mvp` do import agrupado de routers em `01_source/order_pickup_service/app/main.py`.
2. Remover `app.include_router(support.router)` e `app.include_router(support_mvp.router)` de `01_source/order_pickup_service/app/main.py`.
3. Reiniciar `order_pickup_service` e validar `curl -fsS http://localhost:8003/health`.

Owners:

- Primario: @be
- Apoio: @fe
- Validacao: @qa
