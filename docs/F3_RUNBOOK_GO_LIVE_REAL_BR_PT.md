# F-3 Runbook de Go-Live Real (BR/PT)

## Escopo

Runbook operacional para habilitação controlada dos providers reais da Trilha B:

- BR: SVRS/SEFAZ real
- PT: AT real

Com rollback imediato por feature flag e reinício dos serviços fiscais.

## Pré-condições obrigatórias (GO/NO-GO)

Arquivo base para preenchimento rápido de credenciais/flags:

- `02_docker/.env.f3-real.example`
- `02_docker/.env.f3-real.local.example` (simulação de laboratório sem segredos)

Antes de habilitar real em produção/ambiente alvo, validar:

1. Gate BR:

```bash
curl -s "http://localhost:8020/admin/fiscal/providers/br-go-no-go?run_connectivity=true" \
  -H "X-Internal-Token: <TOKEN>"
```

2. Gate PT:

```bash
curl -s "http://localhost:8020/admin/fiscal/providers/pt-go-no-go?run_connectivity=true" \
  -H "X-Internal-Token: <TOKEN>"
```

3. Ambos devem retornar `go_no_go=GO`.
4. Opcional recomendado: preflight consolidado retornar `RESULTADO FINAL: GO`.

## Sequência de habilitação controlada

### Preparar ENV de go-live

1. Criar arquivo de trabalho:

```bash
cp /home/marcos/ellan_lab/02_docker/.env.f3-real.example /home/marcos/ellan_lab/02_docker/.env.f3-real
```

2. Preencher placeholders (`BR/PT host` e `API keys`).
3. Subir serviços fiscais com env-file:

```bash
docker compose --env-file /home/marcos/ellan_lab/02_docker/.env.f3-real \
  -f /home/marcos/ellan_lab/02_docker/docker-compose.yml \
  up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

### Preparar ENV de laboratório (simulação controlada)

1. Criar arquivo local:

```bash
cp /home/marcos/ellan_lab/02_docker/.env.f3-real.local.example /home/marcos/ellan_lab/02_docker/.env.f3-real.local
```

2. Subir serviços fiscais com env-file local:

```bash
docker compose --env-file /home/marcos/ellan_lab/02_docker/.env.f3-real.local \
  -f /home/marcos/ellan_lab/02_docker/docker-compose.yml \
  up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

3. Executar gates em modo laboratório:

```bash
/home/marcos/ellan_lab/02_docker/run_f3_go_no_go.sh
```

4. Executar preflight consolidado (env + gates):

```bash
/home/marcos/ellan_lab/02_docker/run_f3_preflight.sh /home/marcos/ellan_lab/02_docker/.env.f3-real.local.example
```

### Etapa 1 — BR real

1. Ajustar variáveis:

- `FISCAL_REAL_PROVIDER_BR_ENABLED=true`
- `FISCAL_REAL_PROVIDER_BASE_URL_BR=<URL>`
- `FISCAL_REAL_PROVIDER_API_KEY_BR=<KEY>`

2. Reiniciar serviços fiscais:

```bash
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
```

3. Validar em `ops /fiscal/providers`:

- BR com status operacional estável (sem `CRITICAL`)
- metadados de fallback visíveis quando ocorrer contingência.

### Etapa 2 — PT real

1. Ajustar variáveis:

- `FISCAL_REAL_PROVIDER_PT_ENABLED=true`
- `FISCAL_REAL_PROVIDER_BASE_URL_PT=<URL>`
- `FISCAL_REAL_PROVIDER_API_KEY_PT=<KEY>`

2. Reiniciar serviços fiscais (mesmo comando).
3. Validar em `ops /fiscal/providers`:

- PT com status operacional estável (sem `CRITICAL`)
- metadados de fallback visíveis quando ocorrer contingência.

## Rollback imediato por país (one-click operacional)

### Rollback BR

- `FISCAL_REAL_PROVIDER_BR_ENABLED=false`
- reiniciar serviços fiscais (comando acima)

### Rollback PT

- `FISCAL_REAL_PROVIDER_PT_ENABLED=false`
- reiniciar serviços fiscais (comando acima)

### Pós-rollback (obrigatório)

- confirmar gates BR/PT em `NO_GO` ou operação em fallback controlado.
- registrar incidente e ação aplicada (hora, owner, motivo).

## Critérios objetivos de saída ([~] -> [x])

Marcar item BR/PT como `[x]` somente quando TODOS os critérios forem atendidos:

1. gate GO/NO-GO do país com `GO` em execução com conectividade.
2. feature flag real do país habilitada no ambiente alvo.
3. painel `ops /fiscal/providers` sem severidade `CRITICAL` por pelo menos 30 min.
4. caminho de rollback validado (flag false + restart) com evidência registrada.
5. handoff de turno atualizado com owner, janela e ação aplicada.

