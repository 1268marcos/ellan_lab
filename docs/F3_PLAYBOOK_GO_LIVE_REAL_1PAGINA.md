# F-3 Playbook Go-Live Real (1 Pagina)

## Quando usar

Use para virada controlada da Trilha B (BR/PT real) e para rollback imediato em caso de degradação.

## Comandos rápidos

### Gate BR/PT

```bash
curl -s "http://localhost:8020/admin/fiscal/providers/br-go-no-go?run_connectivity=true" -H "X-Internal-Token: <TOKEN>"
curl -s "http://localhost:8020/admin/fiscal/providers/pt-go-no-go?run_connectivity=true" -H "X-Internal-Token: <TOKEN>"
```

### Restart fiscal

```bash
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

## Árvore de decisão

### Caso A: BR/PT = GO

- habilitar flag real do país alvo
- restart fiscal
- monitorar `ops /fiscal/providers` por 30 min

### Caso B: qualquer país = NO_GO

- não habilitar real
- manter fallback/stub
- corrigir pendências e reexecutar gate

### Caso C: degradação após GO (HIGH/CRITICAL)

- rollback imediato por flag (`*_ENABLED=false`)
- restart fiscal
- registrar incidente + handoff

## Checklist de saída ([~] -> [x])

- [ ] gate do país retornou `GO` com conectividade
- [ ] flag real habilitada no ambiente alvo
- [ ] 30 min sem `CRITICAL` no painel providers
- [ ] rollback validado por flag e restart
- [ ] handoff registrado com owner/janela/ação

