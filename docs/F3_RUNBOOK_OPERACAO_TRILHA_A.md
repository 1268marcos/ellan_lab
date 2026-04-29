# F-3 Runbook Operacional (Trilha A - Stub Ready)

## Escopo

Runbook operacional para incidentes e rotina do F-3 com trilha ativa **A (stub-ready)**, cobrindo BR/PT com foco em continuidade operacional.

## Decisao operacional vigente

- Trilha ativa: **A (stub-ready)**
- Motivo: manter velocidade de entrega e estabilidade sem dependencias externas de credenciais oficiais.
- Frontend: **manter JavaScript no curto prazo** para reduzir atrito de entrega.

## Pre-flight diario (2-3 min)

1. Confirmar status de providers:

```bash
curl -s "http://localhost:8020/admin/fiscal/providers/status" \
  -H "X-Internal-Token: <TOKEN>"
```

2. Conferir servicos fiscais no compose:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | rg "billing_fiscal_service|billing_fiscal_issue_worker|billing_fiscal_event_worker"
```

3. Validar painel OPS:

- Abrir `ops /fiscal/providers`
- Verificar `action_severity`, `action_summary` e `rollback_checklist` por pais.

## Acao por severidade (painel providers)

- `OK`: manter monitoramento.
- `WARN`: retestar conectividade e confirmar variaveis de ambiente.
- `HIGH`: preparar fallback operacional e congelar mudancas ate estabilizacao.
- `CRITICAL`: aplicar rollback por pais imediatamente e manter stub como contingencia.

## Rollback rapido BR

1. Manter provider real BR desabilitado (ou retornar para desabilitado):

- `FISCAL_REAL_PROVIDER_BR_ENABLED=false`

2. Reiniciar servicos fiscais:

```bash
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

3. Validar no painel:

- `country=BR` com acao coerente de fallback
- `government_response.raw` contendo `provider_adapter` e `fallback_reason` quando houver fallback.

## Rollback rapido PT

1. Manter provider real PT desabilitado (ou retornar para desabilitado):

- `FISCAL_REAL_PROVIDER_PT_ENABLED=false`

2. Reiniciar servicos fiscais (mesmo comando).
3. Validar no painel:

- `country=PT` com acao coerente de fallback
- metadados de fallback presentes em `government_response.raw`.

## Assinatura A1 dry-run (Trilha A)

Para simulacao de assinatura BR sem provider real:

- `FISCAL_A1_DRY_RUN_ENABLED=true`
- opcional: `FISCAL_A1_DRY_RUN_CERT_REF=<CERT_REF>`

Reiniciar servicos fiscais e validar assinatura marcada como `A1_DRY_RUN`.

## Evidencia minima de plantao

Registrar no fechamento:

- horario inicio/fim
- severidade por pais (BR/PT)
- acao aplicada (retry/fallback/rollback)
- resultado final no painel OPS
- responsavel do turno

