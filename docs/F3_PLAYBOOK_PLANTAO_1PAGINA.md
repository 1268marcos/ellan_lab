# F-3 Playbook de Plantao (1 Pagina)

## Quando usar

Use em incidentes de emissao fiscal BR/PT no fluxo F-3.

## Objetivo em plantao

Restaurar operacao em trilha A (stub-ready) com decisao clara de fallback/rollback por pais.

## Triage rapido (3 min)

1. Status providers:

```bash
curl -s "http://localhost:8020/admin/fiscal/providers/status" -H "X-Internal-Token: <TOKEN>"
```

2. Servicos fiscais de pe:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | rg "billing_fiscal_service|billing_fiscal_issue_worker|billing_fiscal_event_worker"
```

3. Painel OPS:

- abrir `ops /fiscal/providers`
- checar `action_severity` e `action_summary` por pais.

## Arvore de decisao

### Caso A: severidade `OK`

- manter monitoramento
- sem rollback.

### Caso B: severidade `WARN` ou `HIGH`

- retestar conectividade por pais
- se persistir, operar fallback controlado
- congelar mudancas ate estabilizar.

### Caso C: severidade `CRITICAL`

- executar rollback imediato por pais (flag real=false + restart)
- manter stub ate normalizar
- registrar evidencia de incidente.

## Comando unico de restart fiscal

```bash
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

## Checklist de saida

- [ ] painel `ops /fiscal/providers` sem alerta critico ativo
- [ ] acao por pais registrada (BR/PT)
- [ ] fallback/rollback documentado no turno
- [ ] owner de plantao definido

