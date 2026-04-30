# Runbook — incidentes fiscais (ELLAN LAB)

**Escopo:** `billing_fiscal_service`, providers BR (SEFAZ/SVRS) e PT (AT), workers de emissão, filas de e-mail e contingência NFC-e.  
**Audiência:** plantão SRE/OPS + engenharia fiscal.  
**Relacionado:** `docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt`, UI `ops/fiscal/providers`, `fiscal/management-daily`.

---

## 1. Flags e rollback rápido (ordem de leitura)

| Variável | Efeito se `true` / valor | Rollback |
|----------|--------------------------|----------|
| `FISCAL_REAL_PROVIDER_BR_ENABLED` | Cliente HTTP “real” BR (com fallback stub) | `false` + redeploy/restart |
| `FISCAL_REAL_PROVIDER_PT_ENABLED` | Cliente HTTP “real” PT | `false` |
| `FISCAL_A1_DRY_RUN_ENABLED` | NFC-e stub inclui metadados HMAC verificáveis (`A1_DRY_RUN`) | `false` |
| `FISCAL_A1_DRY_RUN_HMAC_SECRET` | Segredo para assinatura dry-run (recomendado em staging partilhado) | Remover ou rotar secret + reemitir testes |
| `INVOICE_SMTP_ENABLED` | SMTP real para DANFE | `false` (volta a stub de e-mail) |

**Regra de ouro:** sem credenciais oficiais SEFAZ/AT, manter **`FISCAL_REAL_PROVIDER_*_ENABLED=false`** em produção assistida.

---

## 2. Árvore de decisão (primeiros 10 minutos)

1. **O incidente afeta só stub / lab?**  
   - Sim → usar endpoints admin de stub (`/admin/fiscal/providers/stub/*`, reset SVRS batch, AT gateway) e logs do serviço.  
   - Não → confirmar flags reais e janela de mudança.

2. **Erro em emissão BR (NFC-e 65)?**  
   - Ver `invoice.government_response`, `sync_pending`, `emission_mode` (`OFFLINE_SAT`, `CONTINGENCY_SVRS`).  
   - Consultar OPS: `/ops/fiscal/providers` + `GET /admin/fiscal/providers/status` (token interno).

3. **Erro em PT?**  
   - Verificar adapter AT + stub gateway F3B (`POST .../stub/at-pt/issue` para contrato isolado).

4. **Timeout / 5xx no client real?**  
   - Esperado: fallback automático para stub (logs `*_failed_fallback_stub`).  
   - Se loop infinito ou fila: reduzir `FISCAL_REAL_PROVIDER_RETRIES`, aumentar timeout ou desligar real.

5. **Fila de e-mail travada?**  
   - Tabela `invoice_email_outbox`, worker de invoice + logs `SENT` / `SENT_STUB` / retries.  
   - Cooldown em `resend` se aplicável.

---

## 3. Sintomas → ações

### 3.1 Provider “down” ou indisponível

- Confirmar health: `GET /admin/fiscal/providers/status` e teste de conectividade se existir na UI.  
- **Ação:** desativar provider real; validar stub; abrir ticket com `order_id` / `invoice_id` / `correlation_id`.

### 3.2 Timeout / 429 / 5xx no provider real

- Logs estruturados + `canonical_error_codes` no status admin.  
- **Ação:** manter fallback; ajustar `FISCAL_REAL_PROVIDER_TIMEOUT_SEC` / retries; se incidente prolongado, **rollback** para stub only.

### 3.3 Rejeição fiscal (código SEFAZ / AT)

- Capturar `provider_code`, `provider_message`, payload bruto em `raw`.  
- **Ação:** não reenviar cegamente; corrigir dados de invoice (NCM, CFOP, destinatário) ou escalar a fiscal domain owner.

### 3.4 Contingência SAT / SVRS + `sync_pending`

- Ver worker `invoice_resync_service` / `sync_pending=true`.  
- **Ação:** consultar runbook técnico de contingência no código (`invoice_resync_service`); testes `F3C-STUB-04` quando existirem.

### 3.5 A1 dry-run (F3C-STUB-01)

- `GET /admin/fiscal/a1-dry-run/status` — flags e algoritmo.  
- `POST /admin/fiscal/a1-dry-run/verify` — corpo `{ "xml_preview": "...", "signature": { ... } }` para validar HMAC local.  
- **Ação:** nunca confundir `A1_DRY_RUN` com XML assinado para SEFAZ.

---

## 4. Checklist de plantão (turno)

- [ ] Confirmar versão/imagem do `billing_fiscal_service` e workers.  
- [ ] Confirmar flags `FISCAL_REAL_PROVIDER_*` e última alteração de env.  
- [ ] Abrir `ops/fiscal/providers` e `fiscal/management-daily` (se contexto contábil).  
- [ ] Identificar `order_id` / `invoice_id` e colar no ticket.  
- [ ] Registrar decisão: rollback stub / hotfix / escalonamento.  
- [ ] **Responsável do turno:** preencher nome no handoff (Slack/wiki interno).

---

## 5. Referências rápidas (API interna)

- **Gate por ambiente (stub vs real):** `GET /admin/fiscal/release-gate/status` — checklist humano: `docs/fiscal_release_gate_checklist.md`
- Status providers: `GET /admin/fiscal/providers/status`  
- A1 dry-run: `GET /admin/fiscal/a1-dry-run/status`, `POST /admin/fiscal/a1-dry-run/verify`  
- Stub SVRS batch: `POST /admin/fiscal/providers/stub/svrs/batch-submit`, `GET .../batch-query`  
- Stub AT PT: `POST /admin/fiscal/providers/stub/at-pt/issue`, `POST .../cancel`, `POST .../reset`  
- Retenção / divergência (contábil): ver rotas `accounting-approvals` no billing fiscal e card D17 em `fiscal/management-daily`.

---

*Última revisão alinhada ao sprint F-3 STUB-READY (F3C-STUB-03 + RELEASE-GATE-01).*

## 6. Legado a verificar (não bloqueia plantão)

- **FA5 / invariantes financeiros:** `tests/test_financial_invariants_fa5.py::test_fa5_sql_invariants_dedupe_and_non_negative` pode falhar em `pytest tests/` completo conforme estado da BD; ver nota em `docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt` (secção *Legado / a verificar*).
