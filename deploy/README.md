# Deploy mínimo e baseline cloud

Este diretório agrupa **artefactos orientados a produto** complementares ao `02_docker/docker-compose.yml` de laboratório.

## Stack mínima (Docker Compose)

O compose principal inclui dezenas de serviços. Para um ambiente de **integração pagamento + runtime + lifecycle + pickup** sem fiscal nem dashboards:

```bash
chmod +x deploy/compose-minimal-stack.sh
./deploy/compose-minimal-stack.sh
```

Reutiliza o mesmo `02_docker/docker-compose.yml` e o mesmo `.env`; apenas limita a lista de serviços arrancados.

## Baseline Kubernetes (GKE/EKS/k3s)

Não há Helm chart oficial neste repositório. O baseline recomendado:

1. **Uma imagem por serviço** — build a partir dos `Dockerfile` já existentes em `01_source/...`.
2. **ConfigMap + Secret** — mapear variáveis do `02_docker/docker-compose.yml` (`ORDER_INTERNAL_TOKEN`, DSN Postgres, URLs internas `http://payment_gateway:8000`, etc.).
3. **Service interno** — rede cluster-only para `payment_gateway`, `order_pickup_service`, `order_lifecycle_service`, `backend_runtime`; Postgres/Redis geridos (RDS/Elasticache ou StatefulSet).
4. **Probes** — reutilizar os mesmos paths de healthcheck do compose (`/health`).

Próximo passo típico de produto: extrair um chart Helm ou Kustomize com um overlay `minimal` e outro `full`.

## Baseline AWS ECS Fargate

1. **Task definition** por serviço (CPU/memória pequenos para staging).
2. **Service Connect** ou **Cloud Map** para DNS interno entre tasks.
3. **Secrets Manager** para tokens e chaves PSP (`MERCADOPAGO_ACCESS_TOKEN`, `STRIPE_*`).

Ficheiro de exemplo (valores placeholder): `deploy/ecs/taskdef-payment-gateway.example.json` — ajustar `image`, `executionRoleArn`, `logConfiguration` antes de usar.

## Testes de contrato (CI / local)

- `make test-collect` — `pytest --collect-only` nos três backends.
- `make test-payment-contract` — executa testes leves gateway→runtime e pickup→lifecycle (sem subir Docker).

Ver `.github/workflows/backend-test-collect.yml` e `.github/workflows/payment-runtime-contract.yml`.

## E2E sobre stack mínima (desenho)

Especificação em camadas (P0 seed + `payment-confirm`, P1 gateway, P2 create order HTTP, P3 UI):  
[`docs/E2E_PAYMENT_MINIMAL_STACK_DESIGN.md`](../docs/E2E_PAYMENT_MINIMAL_STACK_DESIGN.md).

Com a stack no ar: `make e2e-payment-p0` — fluxo **P2** com `POST /orders` (dev bypass lab) + gateway + `payment-confirm`; `E2E_CREATE_ORDER_VIA=seed` volta ao allocate+SQL; `E2E_SKIP_GATEWAY=1` omite o gateway. Locker default SP-Carapicuíba LK-002; slots via runtime, não fixos em 24.
