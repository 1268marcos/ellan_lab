# Checklist — gate fiscal por ambiente (RELEASE-GATE-01)

Objetivo: decisão explícita **stub only** vs **providers reais** (BR/PT) antes de deploy ou ativação em produção assistida.

## 1. Ler estado atual (API)

Com token interno (`X-Internal-Token`):

`GET http://<billing_fiscal_host>:8020/admin/fiscal/release-gate/status`

Campos úteis: `providers.BR.real_provider_enabled`, `providers.PT.real_provider_enabled`, `stub_only_recommended`, `risk_flags`, `rollback_hints`.

## 2. Modo recomendado sem credenciais oficiais

| Variável | Valor seguro |
|----------|----------------|
| `FISCAL_REAL_PROVIDER_BR_ENABLED` | `false` |
| `FISCAL_REAL_PROVIDER_PT_ENABLED` | `false` |
| `FISCAL_A1_DRY_RUN_ENABLED` | `true` apenas em lab se precisar de metadados HMAC; `false` por omissão |
| `INVOICE_SMTP_ENABLED` | `false` até SMTP validado |

## 3. Ativar real BR ou PT (checklist mínimo)

- [ ] URL base e credenciais (`FISCAL_REAL_PROVIDER_BASE_URL_*`, `FISCAL_REAL_PROVIDER_API_KEY_*`) definidas.
- [ ] Timeout/retries alinhados com SRE (`FISCAL_REAL_PROVIDER_TIMEOUT_SEC`, `FISCAL_REAL_PROVIDER_RETRIES`).
- [ ] `risk_flags` vazio no endpoint (sem `*_SEM_BASE_URL_*`).
- [ ] Runbook `docs/runbook_fiscal_incidents.md` revisto para o turno.
- [ ] Rollback: voltar flags a `false` + restart dos pods `billing_fiscal_service` e workers.

## 4. Referência

- Acompanhamento sprint: `docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt`
- Runbook incidentes: `docs/runbook_fiscal_incidents.md`
