# FA-5 Runbook Operacional (Refresh / Rollback / Reconciliação)

## Objetivo

Runbook operacional do FA-5 para:

- manter hypertables/policies Timescale saudáveis,
- executar refresh dos modelos dbt financeiros,
- realizar rollback controlado em incidentes,
- reconciliar divergências de dados financeiros.

Escopo FA-5:

- `ellanlab_revenue_recognition`
- `financial_kpi_daily`
- `ellanlab_monthly_pnl`
- modelos dbt: `partner_revenue_monthly`, `locker_pnl`, `company_mrr_trend`

## Pré-requisitos

- Stack docker em execução (`postgres_central`, `billing_fiscal_service`).
- Extensão Timescale ativa no Postgres.
- Acesso shell ao host com Docker.
- dbt disponível no projeto `dbt_financial` (venv local recomendado).

Comandos base de verificação:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker exec postgres_central psql -U admin -d locker_central -c "SELECT extname, extversion FROM pg_extension WHERE extname='timescaledb';"
```

## 1) Refresh operacional (rotina padrão)

### 1.1 Validar estado Timescale (smoke)

```bash
cd /home/marcos/ellan_lab
./02_docker/run_fa5_timescale_smoke.sh
```

Critério de aceite:

- `SMOKE_OK`
- `hypertable_count = 3`
- `policy_count = 6`
- `dedupe_index_count = 2`

### 1.2 Refresh dos dados FA-5 no billing (recompute diário/mensal)

Use os endpoints admin conforme janela operacional:

- `POST /admin/fiscal/revenue-recognition/recompute?date_ref=YYYY-MM-DD`
- `POST /admin/fiscal/kpi/daily/recompute?date_ref=YYYY-MM-DD`
- `POST /admin/fiscal/pnl/recompute?month=YYYY-MM`

Exemplo (com token interno):

```bash
curl -X POST "http://localhost:8020/admin/fiscal/revenue-recognition/recompute?date_ref=2026-04-28" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/kpi/daily/recompute?date_ref=2026-04-28" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/pnl/recompute?month=2026-04" -H "X-Internal-Token: <TOKEN>"
```

### 1.3 Refresh dos modelos dbt (analytics)

```bash
cd /home/marcos/ellan_lab/01_source/backend/billing_fiscal_service/dbt_financial
. .venv/bin/activate
dbt deps
dbt run --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend
dbt test --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend
```

Critério de aceite:

- `dbt run` sem erros para os 3 models.
- `dbt test` sem falhas.

## 2) Rollback operacional (incidente)

### 2.1 Sintomas típicos

- `SMOKE_FAIL` no bloco FA-5.
- Erros de índices/PK relacionados a hypertable.
- Falha persistente de recompute/dbt após deploy.

### 2.2 Plano de rollback seguro (ordem)

1. **Congelar mutações operacionais** do FA-5 (pausar recomputes em janelas críticas).
2. **Restaurar compatibilidade estrutural Timescale** com script oficial:

```bash
docker cp /home/marcos/ellan_lab/02_docker/postgres_central/ops/enable_fa5_hypertables.sql postgres_central:/tmp/enable_fa5_hypertables.sql
docker exec postgres_central sh -lc "psql -U admin -d locker_central -v ON_ERROR_STOP=1 -f /tmp/enable_fa5_hypertables.sql"
```

3. **Revalidar smoke**:

```bash
cd /home/marcos/ellan_lab
./02_docker/run_fa5_timescale_smoke.sh
```

4. **Reexecutar recomputes** (`revenue-recognition`, `kpi/daily`, `pnl`) para recompor snapshots.
5. **Reexecutar dbt run/test** para recompor camada analytics.

### 2.3 Rollback de aplicação (frontend/backend)

- Se incidente estiver só em UI/admin endpoint, priorizar rollback de aplicação mantendo dados.
- Se incidente for de migração, manter serviço no ar apenas após `SMOKE_OK`.

## 3) Reconciliação financeira (dados)

### 3.1 Reconciliação primária (ledger compat)

Verificar divergências contábeis:

```bash
curl "http://localhost:8020/admin/fiscal/ledger-compat/audit?only_mismatches=true&limit=100" -H "X-Internal-Token: <TOKEN>"
```

Critério:

- reduzir `only_mismatches=true` para zero ou faixa aceitável controlada.

### 3.2 Reconciliação Timescale/FA-5

Verificar endpoint operacional:

```bash
curl "http://localhost:8020/admin/fiscal/timescale/status" -H "X-Internal-Token: <TOKEN>"
```

Critério:

- `smoke_result = SMOKE_OK`
- listas de hypertables/jobs consistentes com o script de smoke.

### 3.3 Reconciliação dbt (camada analytics)

- Garantir `dbt test` em verde.
- Em caso de divergência em KPI/MRR:
  1. Recompute APIs (fonte operacional),
  2. rerun dbt models,
  3. comparar agregados por mês/parceiro.

## 4) Checklists rápidos

### Daily (operação)

- [ ] `run_fa5_timescale_smoke.sh` executado (`SMOKE_OK`)
- [ ] recompute diário (`revenue-recognition`, `kpi/daily`) executado
- [ ] `dbt run/test` da trilha FA-5 executados
- [ ] sem divergências críticas em `ledger-compat/audit?only_mismatches=true`

### Pré-release

- [ ] serviço `billing_fiscal_service` saudável
- [ ] endpoint `/admin/fiscal/timescale/status` retornando smoke `OK`
- [ ] dbt models e testes em verde
- [ ] evidência registrada no acompanhamento de sprint

## 5) Referências operacionais no repositório

- `02_docker/run_fa5_timescale_smoke.sh`
- `02_docker/postgres_central/ops/smoke_fa5_timescale.sql`
- `02_docker/postgres_central/ops/enable_fa5_hypertables.sql`
- `01_source/backend/billing_fiscal_service/dbt_financial/README.md`
