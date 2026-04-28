# FA-5 Playbook de Plantao (1 Pagina)

## Quando usar

Use este playbook quando houver incidente em:

- `/ops/partners/hypertables`
- recompute FA-5 (`revenue-recognition`, `kpi/daily`, `pnl`)
- dashboards/indicadores dbt (`partner_revenue_monthly`, `locker_pnl`, `company_mrr_trend`)

## Objetivo em plantao

Restaurar operacao para estado:

1. `SMOKE_OK` no Timescale FA-5  
2. recompute admin funcionando  
3. dbt run/test em verde  
4. divergencias contabeis sob controle

## Triage rapido (3-5 min)

1) Containers

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

2) Smoke Timescale

```bash
cd /home/marcos/ellan_lab
./02_docker/run_fa5_timescale_smoke.sh
```

3) Endpoint de status

```bash
curl "http://localhost:8020/admin/fiscal/timescale/status" -H "X-Internal-Token: <TOKEN>"
```

## Arvore de decisao

### Caso A: `billing_fiscal_service` DOWN

1. Subir servico:

```bash
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service
```

2. Repetir triage rapido.

### Caso B: `SMOKE_FAIL` no Timescale

1. Reaplicar script de compatibilidade:

```bash
docker cp /home/marcos/ellan_lab/02_docker/postgres_central/ops/enable_fa5_hypertables.sql postgres_central:/tmp/enable_fa5_hypertables.sql
docker exec postgres_central sh -lc "psql -U admin -d locker_central -v ON_ERROR_STOP=1 -f /tmp/enable_fa5_hypertables.sql"
```

2. Rodar smoke novamente.

### Caso C: endpoint admin retorna `403/422`

- Verificar `X-Internal-Token` e alinhar com token ativo do ambiente.
- Em UI, confirmar `VITE_INTERNAL_TOKEN` e reiniciar frontend.

### Caso D: dbt falha (models/tests)

1. Recompute fonte operacional:

```bash
curl -X POST "http://localhost:8020/admin/fiscal/revenue-recognition/recompute?date_ref=<YYYY-MM-DD>" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/kpi/daily/recompute?date_ref=<YYYY-MM-DD>" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/pnl/recompute?month=<YYYY-MM>" -H "X-Internal-Token: <TOKEN>"
```

2. Reexecutar dbt:

```bash
cd /home/marcos/ellan_lab/01_source/backend/billing_fiscal_service/dbt_financial
. .venv/bin/activate
dbt run --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend
dbt test --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend
```

## Checklist de saida de incidente

- [ ] `run_fa5_timescale_smoke.sh` com `SMOKE_OK`
- [ ] `/admin/fiscal/timescale/status` respondendo corretamente
- [ ] recompute endpoints FA-5 executados sem erro
- [ ] `dbt run` (3 models) sem erro
- [ ] `dbt test` sem falhas
- [ ] `ledger-compat/audit?only_mismatches=true` sem aumento anormal de divergencias

## Escalonamento

Escalone se qualquer item abaixo ocorrer por mais de 30 min:

- `SMOKE_FAIL` persistente apos reaplicar `enable_fa5_hypertables.sql`
- erro estrutural de migracao/indice em startup
- discrepancia contábil crescente em `ledger-compat/audit`

Enviar no escalonamento:

- horario inicio/fim
- saida do smoke
- ultimo erro do endpoint/admin
- status dos comandos dbt
- acao ja tentada (comando + resultado)

## Referencias

- Runbook completo: `docs/FA5_RUNBOOK_TIMESCALE_DBT.md`
- Smoke: `02_docker/run_fa5_timescale_smoke.sh`
- SQL smoke: `02_docker/postgres_central/ops/smoke_fa5_timescale.sql`
- Fix hypertables: `02_docker/postgres_central/ops/enable_fa5_hypertables.sql`
