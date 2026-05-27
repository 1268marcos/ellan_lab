# Modo Desenvolvimento - Billing Fiscal Service

## Visão Geral

Este documento descreve como operar o serviço **billing_fiscal_service** em modo desenvolvimento usando stubs fiscais.

---

## Configuração Rápida

1. **Copie** `.env.dev` para `.env`
2. **Ajuste** as variáveis `POSTGRES_*` conforme seu banco local
3. **Execute:**
   ```sh
   docker compose up --build
   ```

---

## Endpoints Úteis em DEV

- **GET /health**  
  Verifica se o serviço está up

- **POST /internal/invoices/generate/{order_id}**  
  Gera uma invoice manualmente para teste

- **GET /internal/invoices/{invoice_id}**  
  Consulta status da invoice

- **POST /admin/fiscal/providers/stub/svrs/smoke-issue/{order_id}**  
  Smoke test "one-click" de emissão fiscal stub

---

## Testando Stubs

### Injeção de Cenários

Adicione no `payload_json` da invoice:

```json
{ "stub_scenario": "AUTHORIZE_TIMEOUT", "stub_success_on_attempt": 2 }
```
Veja demais cenários possíveis no código (`stub_scenario`).

### Consultar Logs dos Stubs

```sh
grep "STUB_FISCAL_OPERATION" logs/app.log | jq
```

---

## Debug Comum

### Invoice não sai de PENDING

1. Verifique se `order.paid` existe em `domain_events`
2. Consulte logs do worker:
   ```sh
   tail -f logs/worker.log
   ```
3. Force reprocessamento via API:
   ```sh
   POST /internal/invoices/{id}/retry
   ```

---

### ConsumerFiscalIncompleteError

1. Complete o perfil fiscal no *order_pickup* **ou**
2. Use `skip_consumer_fiscal_gate=true` no payload **ou**
3. Defina `FISCAL_REQUIRE_COMPLETE_CONSUMER_FOR_REAL_ISSUE=false` no `.env`

---

## Comandos Úteis

### Ver invoices recentes por order

```sh
curl -H "X-Internal-Token: dev-internal-token" http://localhost:8020/internal/invoices/by-order/ord_test_123
```

### Resetar estado dos stubs SVRS batch

```sh
curl -X POST -H "X-Internal-Token: dev-internal-token" http://localhost:8020/admin/fiscal/providers/stub/svrs/batch-reset
```

### Consultar release gate (status feature/provedor real)

```sh
curl -H "X-Internal-Token: dev-internal-token" http://localhost:8020/admin/fiscal/release-gate/status
```

---

## Debug via SQL

### Invoices com erro

```sql
SELECT id, order_id, error_message, last_error_code FROM invoices WHERE status IN ('FAILED', 'DEAD_LETTER');
```

### Gaps de reconciliação abertos

```sql
SELECT gap_type, severity, order_id, invoice_id FROM fiscal_reconciliation_gaps WHERE status = 'OPEN';
```

---

## Flags de Configuração Úteis em DEV

| Variável                  | Valor Recomendado | Efeito                                              |
|---------------------------|-------------------|-----------------------------------------------------|
| `LOG_LEVEL`               | `DEBUG`           | Logs verbosos para debugging                        |
| `STUB_ARTIFICIAL_LATENCY_MS` | `100`         | Simula latência de rede realista                    |
| `DEV_BYPASS_CONSUMER_GATE`   | `true`         | Evita bloqueio por perfil fiscal incompleto         |
| `STUB_DETERMINISTIC_IDS`     | `true`         | UUIDs previsíveis para testes repetíveis            |

---

## Limitações Conhecidas

1. **IDs não são reais:** `access_key`, `protocol_number` são mocks
2. **Sem validação fiscal real:** NCM, CFOP, alíquotas são simplificados
3. **Workers assíncronos:** Alterações podem refletir com atraso de até `INVOICE_ISSUE_POLL_SEC` segundos
4. **Cache em memória:** Falhas injetadas/configs de stub são resetadas ao reiniciar o container

---

## Quando Sair do Modo DEV

Antes de habilitar provider fiscal real:

1. Execute `GET /admin/fiscal/release-gate/status` e valide `go_no_go: GO`
2. Rode smoke test com `STUB_FAILURE_PERCENTAGE=0` e valide 100% de sucesso
3. Valide contrato com:
   ```
   POST /admin/fiscal/stub/validate-contract
   ```
   usando invoices críticas
4. Configure credenciais reais em `.env` e remova as flags `DEV_*`

---

## Checklist Pré-DEV → STAGING

- [ ] Release gate "GO" validado
- [ ] Smoke test (stub) 100% sucesso
- [ ] Falhas forçadas de stub removidas/configuradas
- [ ] Validação de contrato dos invoices principais
- [ ] Variáveis sensíveis e flags DEV revisadas/removidas

---

### Em caso de dúvidas ou troubleshooting: consulte os comandos deste documento.
