# F-3 Checklist Executivo de Operação

## Objetivo

Concluir e operar o F-3 com foco em:

- implementação,
- infraestrutura,
- operação diária,

sem depender de suíte formal de testes nesta fase.

---

## Gate de entrada (decisão obrigatória)

- [x] Definir trilha ativa: **A (stub-ready)** ou **B (real)** conforme credenciais oficiais.
  - **Owner:** Tech Lead Fiscal + Operações
  - **Evidência:** decisão registrada no acompanhamento + variáveis de ambiente por país.
  - **Saída esperada:** trilha escolhida explicitamente para BR/PT.

---

## Trilha A (sem credenciais oficiais)

### 1) F3B-STUB-01 — Provider PT stub dedicado

- [x] Implementar fluxo PT stub (issue/cancel) no contrato canônico.
  - **Owner:** BE-Fiscal
  - **Comando base:**
    ```bash
    docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
    ```
  - **Saída esperada:** emissão/cancelamento PT operando com payload normalizado.

### 2) F3C-STUB-01 — Assinatura A1 dry-run

- [x] Habilitar assinatura em modo dry-run por flag.
  - **Owner:** BE-Fiscal
  - **Comando base:** configurar `A1_DRY_RUN_ENABLED=true` + reiniciar serviços fiscais.
  - **Saída esperada:** XML com metadados de assinatura dry-run persistidos.

### 3) Hardening de operação

- [x] Consolidar painel OPS de providers com status/erro/retry/fallback.
  - **Owner:** BE-Fiscal + FE-OPS
  - **Evidência:** painel `ops /fiscal/providers` acionável em plantão.
  - **Saída esperada:** operação consegue decidir fallback sem intervenção de dev.

---

## Trilha B (com credenciais oficiais)

### 1) SVRS/SEFAZ real (BR)

- [~] Habilitar provider real BR com rollback imediato por flag.
  - **Owner:** BE-Fiscal + SRE/OPS
  - **Comando base:**
    ```bash
    docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service billing_fiscal_issue_worker billing_fiscal_event_worker
    ```
  - **Pré-condição:** `FISCAL_REAL_PROVIDER_BR_ENABLED=true` + credenciais válidas.
  - **Evidência parcial (início controlado):** gate GO/NO-GO em `GET /admin/fiscal/providers/br-go-no-go` e card de decisão no `ops/fiscal/providers`.
  - **Critério objetivo para [x]:**
    - gate BR com `GO` (`run_connectivity=true`);
    - 30 min sem `CRITICAL` em `ops /fiscal/providers`;
    - rollback BR validado por flag (`FISCAL_REAL_PROVIDER_BR_ENABLED=false`) + restart.
  - **Saída esperada:** autorização/cancelamento BR via client real, fallback preservado.

### 2) AT PT real

- [~] Habilitar provider real PT com rollback imediato por flag.
  - **Owner:** BE-Fiscal + SRE/OPS
  - **Comando base:** mesmo deploy/restart da trilha BR.
  - **Pré-condição:** `FISCAL_REAL_PROVIDER_PT_ENABLED=true` + credenciais válidas.
  - **Evidência parcial (início controlado):** gate GO/NO-GO em `GET /admin/fiscal/providers/pt-go-no-go` e card de decisão no `ops/fiscal/providers`.
  - **Critério objetivo para [x]:**
    - gate PT com `GO` (`run_connectivity=true`);
    - 30 min sem `CRITICAL` em `ops /fiscal/providers`;
    - rollback PT validado por flag (`FISCAL_REAL_PROVIDER_PT_ENABLED=false`) + restart.
  - **Saída esperada:** emissão/cancelamento PT via provider real com normalização de erros.

---

## Bloco obrigatório (vale para A e B)

### Rollback

- [x] Publicar e validar rollback por país (BR/PT).
  - **Owner:** SRE/OPS
  - **Saída esperada:** rollback one-click operacional.

### Runbook e Playbook

- [x] Atualizar documentação de operação conforme trilha ativa.
  - **Owner:** SRE/OPS + BE-Fiscal
  - **Evidência:** `docs/F3_RUNBOOK_OPERACAO_TRILHA_A.md`, `docs/F3_PLAYBOOK_PLANTAO_1PAGINA.md`, `docs/F3_RUNBOOK_GO_LIVE_REAL_BR_PT.md` e `docs/F3_PLAYBOOK_GO_LIVE_REAL_1PAGINA.md`.
  - **Saída esperada:** instrução única e clara para plantão.

### Handoff de operação

- [x] Concluir handoff com responsável de turno.
  - **Owner:** Operações
  - **Evidência:** bloco de handoff pronto + exemplo preenchido no acompanhamento.
  - **Saída esperada:** plantão autônomo para incidentes F-3.

---

## Critério de fechamento do F-3 (operação)

- [ ] Fluxo fiscal BR/PT estável na trilha escolhida.
- [ ] Feature flags de go-live/rollback documentadas e operáveis.
- [x] Painel OPS com indicadores de ação (erro/latência/fallback).
- [x] Runbook/playbook atualizados.
- [x] Evidência registrada no acompanhamento com data/hora/owner.
