# ELLAN LAB - Sprints Products, Partners e Lockers

Documento de acompanhamento para evolucao do fluxo de catalogo, elegibilidade e alocacao em lockers com base no schema `02_docker/complete_schema_20260427_c.sql`.

Data de criacao: 27/04/2026  
Status geral: [x] Concluido — **Sprint 12** encerrado (checklist de implantacao do **capitulo 10** fechado com evidencias). *Nota: o sprint **numerado 10** da API (`top-divergences`) ja consta como concluido no registro abaixo; nao e reaberto.*

---

## Legenda de status (preencher ao longo dos sprints)

[ ] Nao iniciado   [~] Em andamento   [x] Concluido   [!] Bloqueado / risco

---

## 1) Objetivo e metas

### Objetivo principal
Implementar um fluxo ponta a ponta para produtos de parceiros em lockers, cobrindo cadastro, elegibilidade, alocacao, reserva, pickup e settlement.

### Metas de resultado
- Disponibilizar catalogo funcional em `products` com governanca de status (`DRAFT` -> `ACTIVE`).
- Garantir elegibilidade por parceiro/locker via `partner_service_areas`, `locker_slot_configs` e `product_locker_configs`.
- Reduzir falhas de alocacao concorrente com estrategia atomica (`FOR UPDATE SKIP LOCKED`).
- Evitar oversell com controle de estoque em `product_inventory` e `inventory_reservations`.
- Fechar ciclo de parceiro com notificacao confiavel (`partner_order_events_outbox`) e settlement (`partner_settlement_batches`).

---

## Status do sprint atual

- **Sprint atual**: **Sprint 12** — Checklist de implantacao (**`## 10) Checklist de implantacao`**) finalizado; backlog evolutivo segue no Sprint 13.
- **Status**: [x] Concluido
- **Data de inicio Sprint 12**: 27/04/2026
- **Sprint anterior**: [x] Sprint 11 encerrado (reconciliacao executiva OPS).
- **Itens de produto (historico — concluidos)**:
  - [x] US-PPL-001 - Fundacao de lockers e slots (Sprint 0 fechado)
  - [x] US-PPL-002 - Vinculo parceiro e area de atendimento (Sprint 0 fechado)
  - [x] US-PPL-003 - Catalogo de produto com validacao de elegibilidade
  - [x] US-PPL-004 - Alocacao atomica de slot
  - [x] US-PPL-005 - Inventario, reserva e expiracao
  - [x] US-PPL-006 - Pickup e liberacao do slot
  - [x] US-PPL-007 - Entrega de eventos para parceiro (outbox)
  - [x] US-PPL-008 - Settlement mensal de parceiros (Sprints 6-10 API + hardening: geracao, itens, approve/pay, reconciliacao OPS)
  - [x] Hardening operacional - reconciliacao e comite (Sprints 7-10 entregues)
  - [x] Sprint 11 - refinamentos de leitura executiva (`min_severity`, `severity_counts`, DoD tecnico, SQL de limpeza de batches legados de teste)
- **Itens ativos Sprint 12 (kickoff)**:
  - [x] Percorrer **`## 10) Checklist de implantacao`**: linhas fechadas com evidencia (comando, log e registro de UX/CX).
  - [x] Priorizar itens ja parcialmente verdadeiros em lab (seeds, parceiros, settlement) antes de carga/WCAG — **dia 0** executado (ver registro `Sprint 12: registro dia 0`).
  - [x] Pagina OPS de reconciliacao entregue (evoluida alem do minimo): `top-divergences` + `compare` + visualizacoes operacionais e filtros guiados.

---

## Registro direto de execucao (solo dev + apoio IA)

### 27/04/2026 - Kickoff tecnico Sprint 0
- [x] Registro de kickoff feito neste documento.
- [x] Script de seed Sprint 0 criado em `01_source/order_pickup_service/scripts/sprint0_seed_products_partners_lockers.py`.
- [x] SQL oficial do Sprint 0 criado em `03_data/scripts_sql/hotfix/20260427_sprint0_products_partners_lockers_seed.sql`.
- [x] SQL de validacao do Sprint 0 criado em `03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql`.
- [~] US-PPL-001 em execucao:
  - materializacao idempotente de `locker_slots` a partir de `locker_slot_configs`.
  - sincronizacao de `lockers.slots_count` e `lockers.slots_available`.
- [~] US-PPL-002 em execucao:
  - upsert de parceiros base em `ecommerce_partners` (`OP-ELLAN-001`, `OP-PHARMA-001`).
  - associacao idempotente em `partner_service_areas` por pais e regras de prioridade/exclusividade.

### Como executar agora (Sprint 0 - caminho oficial)
```bash
# executar a partir da raiz do repo: /home/marcos/ellan_lab
psql "$DATABASE_URL" -f 03_data/scripts_sql/hotfix/20260427_sprint0_products_partners_lockers_seed.sql
psql "$DATABASE_URL" -f 03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql
```

### Se der erro no `psql` com role local (ex.: `role "marcos" does not exist`)
- Causa comum: `DATABASE_URL` vazio ou sem credenciais; o `psql` tenta conectar no socket local com usuario do SO.
- Validar variavel:
```bash
echo "$DATABASE_URL"
```
- Exemplo com URL completa:
```bash
psql "postgresql://SEU_USUARIO:SUA_SENHA@SEU_HOST:5432/SEU_BANCO" -f 03_data/scripts_sql/hotfix/20260427_sprint0_products_partners_lockers_seed.sql
psql "postgresql://SEU_USUARIO:SUA_SENHA@SEU_HOST:5432/SEU_BANCO" -f 03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql
```
- Exemplo com parametros separados:
```bash
PGPASSWORD="SUA_SENHA" psql -h SEU_HOST -p 5432 -U SEU_USUARIO -d SEU_BANCO -f 03_data/scripts_sql/hotfix/20260427_sprint0_products_partners_lockers_seed.sql
PGPASSWORD="SUA_SENHA" psql -h SEU_HOST -p 5432 -U SEU_USUARIO -d SEU_BANCO -f 03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql
```

### Opcional (execucao via Python service layer)
```bash
cd 01_source/order_pickup_service
python -m app.core.db_migrations
python scripts/sprint0_seed_products_partners_lockers.py
```

### Evidencias esperadas apos execucao
- `locker_slots` preenchida para lockers com configuracao em `locker_slot_configs`.
- `ecommerce_partners` contendo os parceiros base ativos do Sprint 0.
- `partner_service_areas` com cobertura ativa por parceiro/locker.
- Resultado das consultas de validacao em `03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql`.

### Checklist de leitura dos SELECT (fechamento formal Sprint 0)
- [x] **Q1 Parceiros base**: `OP-ELLAN-001` e `OP-PHARMA-001` presentes, `active=true`, `status=ACTIVE`.
- [x] **Q2 Slots materializados**: lockers com `total_slots > 0` e `available_slots >= 0`.
- [x] **Q3 Consistencia lockers x slots**: `slots_count == slots_materializados` e `slots_available == slots_disponiveis_materializados` para lockers ativos.
- [x] **Q4 Cobertura ativa por parceiro**: ambos parceiros com `active_links > 0`.
- [x] **Q5 Lista de atendimento**: links ativos em `partner_service_areas` com `valid_from` preenchido e prioridade coerente (`ELLAN=100`, `PHARMA=200` quando aplicavel).
- [x] **Decisao de fechamento Sprint 0**: fechar Sprint 0 e iniciar Sprint 1.

### Resultado desta rodada (preencher apos execucao no banco)
- [x] **Execucao dos 5 SELECTs concluida** via:
  - `PGPASSWORD="admin123" psql -h localhost -p 5435 -U admin -d locker_central -f 03_data/scripts_sql/select/20260427_sprint0_products_partners_lockers_validation.sql`
- [x] **Q1 confirmado**: parceiros base ativos (`OP-ELLAN-001`, `OP-PHARMA-001`).
- [x] **Q2 confirmado**: 13 lockers com slots materializados (>0).
- [x] **Q3 confirmado**: sem divergencia para lockers ativos retornados na checagem.
- [x] **Q4 confirmado**: `active_links` > 0 para os dois parceiros.
- [x] **Q5 confirmado**: prioridades coerentes (`ELLAN=100`, `PHARMA=200`) e `valid_from` preenchido.
- [x] **Fechamento formal Sprint 0**: concluido.

### 27/04/2026 - Inicio Sprint 1 (US-PPL-003)
- [x] Endpoint inicial implementado: `POST /partners/{partner_id}/products`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Validacoes implementadas no endpoint:
  - parceiro deve estar com status `ACTIVE`;
  - `category_id` deve existir em `product_categories`;
  - elegibilidade deve existir em pelo menos um locker ativo do parceiro (join entre `partner_service_areas`, `locker_slot_configs` e `product_locker_configs.allowed=true`);
  - `products.id` nao pode estar duplicado.
- [x] Persistencia implementada:
  - insert de produto em `products` com `status='DRAFT'` e `is_active=false`;
  - registro de trilha inicial em `product_status_history` (`NULL -> DRAFT`).
- [x] Resposta implementada:
  - `recommended_locker_id`,
  - `recommended_slot_size`,
  - `eligible_lockers_count`.
- [x] Validacao de pre-condicao no banco (Sprint 1):
  - `OP-ELLAN-001`: 5 lockers com area + 5 com regra de categoria permitida.
  - `OP-PHARMA-001`: 1 locker com area + 1 com regra de categoria permitida.
- [x] Teste HTTP real executado com `OPS_TOKEN` (após restart dos containers):
  - **Sucesso (`200`)**:
    - endpoint: `POST /partners/OP-ELLAN-001/products`
    - payload: SKU `SKU-SPRINT1-1777317084`, categoria `ELECTRONICS`, dimensoes `120x120x120`, peso `800g`
    - retorno: `status=DRAFT`, `eligibility_ok=true`, `recommended_locker_id=SP-ALPHAVILLE-SHOP-LK-001`, `recommended_slot_size=M`, `eligible_lockers_count=4`
  - **Bloqueio esperado (`422 PRODUCT_NOT_ELIGIBLE`)**:
    - endpoint: `POST /partners/OP-ELLAN-001/products`
    - payload: SKU `SKU-SPRINT1-NEG-1777317093`, dimensoes/peso fora da capacidade (`9999mm`, `999999g`)
    - retorno: `type=PRODUCT_NOT_ELIGIBLE`
- [~] Proximo passo imediato:
  - implementar endpoint de elegiveis por locker no backlog do Sprint 1;
  - iniciar gate fiscal para transicao `DRAFT -> ACTIVE`.

### 27/04/2026 - Sprint 1 item seguinte (elegiveis por locker)
- [x] Endpoint implementado: `GET /partners/{partner_id}/lockers/{locker_id}/eligible-products`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Regras implementadas:
  - parceiro precisa estar `ACTIVE`;
  - locker precisa estar em `partner_service_areas` ativa/vigente para o parceiro;
  - somente produtos `ACTIVE`;
  - produto elegivel apenas se categoria permitida (`product_locker_configs.allowed=true`) e dimensoes/peso couberem no locker (`locker_slot_configs`);
  - retorno com `recommended_slot_size` por produto.
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /partners/OP-ELLAN-001/lockers/SP-ALPHAVILLE-SHOP-LK-001/eligible-products?limit=20&offset=0`
    - retorno: `total=1`, item `SKU-SPRINT1-1777317084`, `recommended_slot_size=M`
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/OP-ELLAN-001/lockers/PT-MAIA-CENTRO-LK-001/eligible-products`
    - retorno: `type=LOCKER_NOT_IN_PARTNER_SERVICE_AREA`
- [x] Ajuste de dado para teste:
  - produto `SKU-SPRINT1-1777317084` promovido para `ACTIVE` no banco para validar listagem de elegiveis.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Inicio Sprint 2 (US-PPL-004: alocacao atomica)
- [x] Endpoint implementado: `POST /partners/{partner_id}/lockers/{locker_id}/slot-allocations/pick`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Regra tecnica principal implementada:
  - selecao atomica do melhor slot em `locker_slots` com `FOR UPDATE SKIP LOCKED`;
  - ordenacao por menor slot compativel e menor recencia de abertura;
  - update transacional do slot para `OCCUPIED` com `current_allocation_id`.
- [x] Guardrails de negocio:
  - parceiro `ACTIVE`;
  - locker dentro de `partner_service_areas` ativa/vigente;
  - produto existente e `ACTIVE`;
  - categoria permitida e dimensoes/peso compativeis.
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `POST /partners/OP-ELLAN-001/lockers/SP-ALPHAVILLE-SHOP-LK-001/slot-allocations/pick`
    - payload: `{\"product_id\":\"SKU-SPRINT1-1777317084\"}`
    - retorno: `allocation_id=al_3ae8dacdc9e9458a9ebc8239`, `slot_label=M-001`, `state=RESERVED_PENDING_PAYMENT`
  - **Bloqueio esperado (`422`)**:
    - `POST /partners/OP-ELLAN-001/lockers/PT-MAIA-CENTRO-LK-001/slot-allocations/pick`
    - retorno: `type=LOCKER_NOT_IN_PARTNER_SERVICE_AREA`
- [x] Incidente tecnico encontrado e resolvido nesta rodada:
  - trigger de banco `trg_log_slot_state_change` quebrada (referencia `NEW.metadata` inexistente) causando `500` em update de `locker_slots`;
  - hotfix aplicado diretamente no banco para restaurar logging de transicao de estado sem depender da coluna inexistente.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Avanco Sprint 3 (US-PPL-005: expiracao operacional sob demanda)
- [x] Endpoint OPS implementado: `POST /ops/inventory/reservations/expire/run`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/inventory.py`
  - `01_source/order_pickup_service/app/schemas/inventory.py`
- [x] Comportamento entregue:
  - executa o job `run_inventory_reservations_expiry_once` sob demanda para operacao/auditoria;
  - retorna payload executivo com `changed` para leitura rapida de impacto.
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar novo endpoint no container).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Reserva criada (`200`)** em `POST /inventory/reserve` para preparar cenario ativo.
  - **Execucao do job (`200`)** em `POST /ops/inventory/reservations/expire/run` com retorno `{\"ok\":true,\"changed\":1,...}`.
- [x] Validacao SQL pos-job:
  - `inventory_reservations.status` atualizado para `EXPIRED`.
  - `product_inventory.quantity_reserved` retornou para `0` no item testado.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Fechamento US-PPL-005 + item seguinte Sprint 3 (visao diaria/comite)
- [x] Endpoint implementado: `GET /ops/inventory/reservations`.
- [x] Filtros operacionais entregues:
  - `status` (`ACTIVE|EXPIRED|RELEASED|CONSUMED|CANCELLED`);
  - `period_from` e `period_to` (janela por `updated_at`);
  - `locker_id`, `product_id`, `order_id`, `limit`, `offset`.
- [x] Validacao HTTP real:
  - **Sucesso (`200`)**:
    - `GET /ops/inventory/reservations?status=EXPIRED&period_from=2026-04-27T00:00:00Z&period_to=2026-04-28T00:00:00Z&limit=3&offset=0`
    - retorno com `total=1` e reserva `3af40cd9-4762-462c-ab10-8cf62a99822d`.
  - **Bloqueio esperado (`422`)**:
    - `GET /ops/inventory/reservations?status=INVALID`
    - retorno: `type=INVALID_RESERVATION_STATUS`.
- [x] Item seguinte Sprint 3 iniciado/entregue:
  - endpoint de alerta operacional: `GET /ops/inventory/low-stock` (threshold configuravel para leitura rapida de risco de ruptura).
- [x] Validacao HTTP real do item seguinte:
  - `GET /ops/inventory/low-stock?threshold=20&limit=3&offset=0`
  - retorno com `total=1` (item `cookie_laranja` no locker `SP-OSASCO-CENTRO-LK-001`).
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoints novos).
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Inicio Sprint 4 (US-PPL-006: confirmacao de retirada + liberacao transacional)
- [x] Endpoint operacional implementado:
  - `POST /partners/{partner_id}/lockers/{locker_id}/slot-allocations/{allocation_id}/pickup-confirm`
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Comportamento entregue (transacional):
  - valida parceiro `ACTIVE` e vinculo ativo em `partner_service_areas`;
  - bloqueia `allocations` + `locker_slots` em transacao;
  - confirma retirada atualizando `allocations.state -> PICKED_UP`;
  - conclui pickup (`pickups.status -> REDEEMED`, `redeemed_via=OPERATOR`);
  - conclui pedido (`orders.status -> PICKED_UP`);
  - libera slot fisico (`locker_slots.status -> AVAILABLE`, `current_allocation_id -> NULL`).
- [x] Idempotencia:
  - nova chamada para allocation ja confirmada retorna `idempotent=true`.
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para expor endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `POST /partners/OP-ELLAN-001/lockers/SP-OSASCO-CENTRO-LK-001/slot-allocations/al_f3db401e25514cf88bb73958b402d5f3/pickup-confirm`
    - retorno com `allocation_state=PICKED_UP`, `pickup_status=REDEEMED`, `order_status=PICKED_UP`.
  - **Bloqueio esperado (`422`)**:
    - mesmo `allocation_id` em locker fora da area ativa do parceiro (`PT-MAIA-CENTRO-LK-001`);
    - retorno: `type=LOCKER_NOT_IN_PARTNER_SERVICE_AREA`.
  - **Idempotencia (`200`)**:
    - segunda confirmacao no mesmo endpoint retorna `idempotent=true`.
- [x] Validacao SQL pos-endpoint:
  - `allocations.state = PICKED_UP`
  - `pickups.status = REDEEMED` e `lifecycle_stage = COMPLETED`
  - `orders.status = PICKED_UP`
  - `locker_slots.status = AVAILABLE` e `current_allocation_id IS NULL`
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Inicio Sprint 5 (US-PPL-007: priorizacao operacional de dead-letter)
- [x] Endpoint OPS implementado:
  - `GET /ops/integration/order-events-outbox/dead-letter-priority`
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/integration_ops.py`
  - `01_source/order_pickup_service/app/schemas/integration_ops.py`
- [x] Entrega funcional:
  - ranking de dead-letter por `partner_id` + `event_type`;
  - resumo executivo com `total_dead_letters`, `total_distinct_orders` e `total_groups`;
  - suporte a filtros operacionais: `partner_id`, `event_type`, `period_from`, `period_to`.
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para expor endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /ops/integration/order-events-outbox/dead-letter-priority?limit=5`
    - retorno com `total_dead_letters=10`, `total_groups=5` e ranking priorizado por volume.
  - **Bloqueio esperado (`422`)**:
    - `GET /ops/integration/order-events-outbox/dead-letter-priority?period_from=2026-04-28T00:00:00Z&period_to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 5 (US-PPL-007): replay em lote focado por top N de impacto + KPIs
- [x] Endpoint implementado:
  - `POST /ops/integration/order-events-outbox/replay-priority-groups`
- [x] Capacidade entregue:
  - selecao automatica de **top N grupos prioritarios** (`partner_id + event_type`) baseada em volume `DEAD_LETTER` e `distinct_orders`;
  - `dry_run=true` para simulacao segura antes da acao;
  - execucao controlada com `max_items` e guardrails para `run_after_replay`;
  - opcao de disparar worker apos replay (`run_after_replay`) com limite operacional.
- [x] Estrutura nova para indicadores/KPIs criada via migration:
  - tabela: `ops_outbox_replay_priority_runs`
  - indices: `idx_oorp_runs_created_at`, `idx_oorp_runs_dry_mode`
  - persistencia por execucao: filtros, grupos selecionados, total candidatos, replayed/skipped e payload do worker.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/integration_ops.py`
  - `01_source/order_pickup_service/app/schemas/integration_ops.py`
  - `01_source/order_pickup_service/app/core/db_migrations.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para aplicar migration e expor endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Dry-run (`200`)**:
    - `POST /ops/integration/order-events-outbox/replay-priority-groups?dry_run=true&top_n_groups=3&max_items=10`
    - retorno com `execution_id`, grupos priorizados e `replayed_count=0`.
  - **Guardrail (`422`)**:
    - `POST ...?dry_run=true&run_after_replay=true`
    - retorno: `type=INVALID_RUN_AFTER_REPLAY`.
  - **Execucao controlada real (`200`)**:
    - `POST ...?dry_run=false&run_after_replay=false&top_n_groups=1&max_items=2`
    - retorno com `replayed_count=2` (status atualizado para `PENDING`).
- [x] Validacao SQL de KPI:
  - tabela `ops_outbox_replay_priority_runs` criada e populada com execucoes dry-run e execucao real.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 5 (US-PPL-007): consulta historica de runs (timeline + taxa de efetividade)
- [x] Endpoint implementado:
  - `GET /ops/integration/order-events-outbox/replay-priority-groups/runs`
- [x] Capacidade entregue:
  - timeline paginada de execucoes (`limit`/`offset`) dos runs de replay prioritario;
  - filtros por periodo (`period_from`, `period_to`) e `dry_run`;
  - calculo de `effectiveness_rate_pct` por execucao (`replayed_count / selected_count`);
  - indicador consolidado `average_effectiveness_rate_pct` para leitura executiva.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/integration_ops.py`
  - `01_source/order_pickup_service/app/schemas/integration_ops.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /ops/integration/order-events-outbox/replay-priority-groups/runs?limit=10`
    - retorno com 2 execucoes, incluindo `effectiveness_rate_pct` (100.0 e 0.0) e media `20.0`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - KPIs adicionais em sprints anteriores (analise + implementacao)
- [x] Avaliacao dos sprints 0-4:
  - Sprint 0/1/2/3 ja possuem indicadores operacionais diretos por listagem/monitoramento (elegibilidade, reservas, low stock, dead-letter prioritization).
  - **Gap identificado no Sprint 4**: faltava KPI dedicado para taxa de efetividade de confirmacao de retirada.
- [x] KPI implementado para Sprint 4:
  - endpoint: `GET /partners/ops/pickup-confirm/metrics`
  - metrica entregue: `total_calls`, `total_success`, `total_error`, `success_rate_pct`, `idempotent_calls`, `effective_calls`, `idempotent_rate_pct`.
  - fonte dos dados: trilha de auditoria em `ops_action_audit` com acao `PARTNER_SLOT_PICKUP_CONFIRM`.
- [x] Ajuste tecnico para viabilizar indicador:
  - auditoria adicionada no endpoint `POST /partners/{partner_id}/lockers/{locker_id}/slot-allocations/{allocation_id}/pickup-confirm`, incluindo chamadas idempotentes e efetivas.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo e ajuste de auditoria).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /partners/ops/pickup-confirm/metrics`
    - retorno inicial com taxa correta e contabilizacao de chamada idempotente.
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/ops/pickup-confirm/metrics?period_from=2026-04-28T00:00:00Z&period_to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 4 (US-PPL-006): compare entre janelas para KPI de pickup
- [x] Endpoint implementado:
  - `GET /partners/ops/pickup-confirm/metrics/compare`
- [x] Capacidade entregue:
  - comparativo **current vs previous** com mesma duracao de janela;
  - retorno estruturado com blocos `current` e `previous`;
  - deltas executivos: `delta_calls_pct`, `delta_effective_calls_pct`, `delta_success_rate_pct`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /partners/ops/pickup-confirm/metrics/compare`
    - retorno com `current`, `previous` e deltas de volume/efetividade/sucesso.
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/ops/pickup-confirm/metrics/compare?period_from=2026-04-28T00:00:00Z&period_to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 6 (US-PPL-008): fechamento de settlement sem pendencias
- [x] Pendencias revisadas de sprints anteriores:
  - mantidos os entregaveis de Sprint 0-5 como concluidos;
  - sem bloqueio novo encontrado nos endpoints operacionais ja entregues.
- [x] Evolucao de settlement implementada:
  - geracao de batch agora popula `partner_settlement_items` no mesmo periodo do batch;
  - endpoint novo de auditoria de itens do lote:
    - `GET /partners/{partner_id}/settlements/{batch_id}/items`
  - endpoint novo para fechar ciclo financeiro:
    - `PATCH /partners/{partner_id}/settlements/{batch_id}/pay` (transicao `APPROVED -> PAID`).
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoints novos).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `POST /partners/OP-ELLAN-001/settlements/generate` (batch criado em `DRAFT`);
    - `GET /partners/OP-ELLAN-001/settlements/{batch_id}/items?limit=5` (timeline de itens/totalizadores);
    - `PATCH /partners/OP-ELLAN-001/settlements/{batch_id}/approve` seguido de `PATCH .../pay` (status final `PAID`).
  - **Bloqueio esperado (`422`)**:
    - `PATCH /partners/OP-ELLAN-001/settlements/{batch_id}/pay` antes de aprovar;
    - retorno: `type=INVALID_SETTLEMENT_STATUS_TRANSITION`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 7 (Hardening): reconciliacao automatica batch vs items + alerta para comite
- [x] Endpoint implementado:
  - `GET /partners/{partner_id}/settlements/{batch_id}/reconciliation`
- [x] Capacidade entregue:
  - compara totais esperados do `partner_settlement_batches` com somatorio real de `partner_settlement_items`;
  - calcula deltas de pedidos, gross e revenue share (`delta_total_orders`, `delta_gross_revenue_cents`, `delta_revenue_share_cents`);
  - marca `has_divergence=true` quando houver mismatch;
  - gera alerta operacional com severidade e mensagem de escalonamento para comite (`SETTLEMENT_RECONCILIATION_DIVERGENCE`);
  - registra auditoria em `ops_action_audit` com acao `PARTNER_SETTLEMENT_RECONCILIATION_CHECK`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso sem divergencia (`200`)**:
    - `GET /partners/OP-ELLAN-001/settlements/{batch_id}/reconciliation`
    - retorno com `has_divergence=false` e `alerts=[]`.
  - **Sucesso com divergencia e alerta (`200`)**:
    - inserido item sintetico de teste em `partner_settlement_items` do batch;
    - retorno com `has_divergence=true`, deltas positivos e alerta `SETTLEMENT_RECONCILIATION_DIVERGENCE` (severity `HIGH`).
    - limpeza executada apos teste para nao deixar lixo na base.
  - **Nao encontrado (`404`)**:
    - batch inexistente retorna `type=SETTLEMENT_NOT_FOUND`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 7 (Hardening): timeline de alertas de reconciliacao para comite operacional
- [x] Endpoint implementado:
  - `GET /partners/ops/settlements/reconciliation-alerts`
- [x] Capacidade entregue:
  - lista historica paginada de alertas de divergencia de reconciliacao;
  - filtros por periodo (`from`, `to`) e `partner_id`;
  - retorno com severidade, mensagem e deltas financeiros/quantitativos por ocorrencia;
  - pronto para ritual de comite e priorizacao de correcao.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - criacao de divergencia sintetica de teste + chamada `GET /partners/ops/settlements/reconciliation-alerts?limit=5`;
    - retorno com itens de alerta, `severity=HIGH` e deltas de reconciliacao.
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/ops/settlements/reconciliation-alerts?from=2026-04-28T00:00:00Z&to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
  - limpeza aplicada apos teste sintetico para nao deixar lixo em base.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 8: execucao em lote segura da reconciliacao (runbook operacional)
- [x] Endpoint implementado:
  - `POST /partners/ops/settlements/reconciliation/run`
- [x] Capacidade entregue:
  - executa reconciliacao em lote por periodo/parceiro com limite de batches;
  - modo seguro com `dry_run=true` por padrao;
  - retorno executivo com `scanned_batches`, `divergent_batches` e `divergence_rate_pct`;
  - quando `dry_run=false`, registra trilha de auditoria `PARTNER_SETTLEMENT_RECONCILIATION_BATCH_RUN`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `POST /partners/ops/settlements/reconciliation/run?dry_run=true&limit=20`
    - `POST /partners/ops/settlements/reconciliation/run?dry_run=false&limit=20`
  - **Bloqueio esperado (`422`)**:
    - `POST /partners/ops/settlements/reconciliation/run?from=2026-04-28T00:00:00Z&to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 8 (hardening seguro): guardrails para execucao real do batch run
- [x] Endurecimento de seguranca aplicado no endpoint:
  - `POST /partners/ops/settlements/reconciliation/run`
- [x] Regras novas de protecao:
  - `dry_run=false` agora exige confirmacao explicita `confirm_live_run=true`;
  - execucao real possui limite operacional restrito (`limit <= 200`);
  - `dry_run=true` permanece caminho padrao e seguro.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar novos guardrails).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `POST .../reconciliation/run?dry_run=true&limit=20`
    - `POST .../reconciliation/run?dry_run=false&confirm_live_run=true&limit=20`
  - **Bloqueios esperados (`422`)**:
    - sem confirmacao: `type=LIVE_RUN_CONFIRMATION_REQUIRED`
    - limite alto em live run: `type=LIVE_RUN_LIMIT_EXCEEDED`
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 9: comparativo entre janelas para reconciliacao em lote (governanca executiva)
- [x] Endpoint implementado:
  - `GET /partners/ops/settlements/reconciliation/compare`
- [x] Capacidade entregue:
  - comparativo **current vs previous** para reconciliacao financeira;
  - metricas por janela: `scanned_batches`, `divergent_batches`, `divergence_rate_pct`;
  - deltas executivos: `delta_scanned_batches_pct`, `delta_divergent_batches_pct`, `delta_divergence_rate_pct`;
  - suporte a filtro por `partner_id`.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /partners/ops/settlements/reconciliation/compare`
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/ops/settlements/reconciliation/compare?from=2026-04-28T00:00:00Z&to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Seed de banco necessario para esta etapa? **Nao** (dados atuais suficientes para validacao base).
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Sprint 10: priorizacao de divergencias por impacto (top N)
- [x] Endpoint implementado:
  - `GET /partners/ops/settlements/reconciliation/top-divergences`
- [x] Capacidade entregue:
  - ranking dos batches divergentes por `impact_score` (peso financeiro + quantitativo);
  - foco operacional no topo de risco para acao rapida do comite;
  - filtros por periodo e `partner_id`, com `top_n` configuravel.
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim**.
  - executado: `docker compose up -d --build order_pickup_service` (necessario para carregar endpoint novo).
- [x] Testes HTTP reais (com `OPS_TOKEN`):
  - **Sucesso (`200`)**:
    - `GET /partners/ops/settlements/reconciliation/top-divergences?top_n=5`
  - **Bloqueio esperado (`422`)**:
    - `GET /partners/ops/settlements/reconciliation/top-divergences?from=2026-04-28T00:00:00Z&to=2026-04-27T00:00:00Z`
    - retorno: `type=INVALID_DATE_RANGE`.
- [x] Seed de banco necessario para esta etapa? **Nao** para validar contrato/seguranca.
  - opcionalmente, para validar ranking com massa real de divergencia, posso te passar SQL minimo de seed controlado.
- [x] Pagina nova criada neste passo? **Nao** (apenas backend/API).

### 27/04/2026 - Ajuste: severidade de divergencia (reconciliacao de settlements)
- [x] Regra alinhada ao comite: **HIGH** apenas quando ha divergencia em `gross_revenue_cents` (batch vs soma dos itens); divergencia so em contagem de itens ou em share (sem divergencia em gross) e **MEDIUM**; quando nao ha delta em gross nem em contagem e so ha resíduo pequeno em share (`abs(delta_revenue_share_cents)` menor que 10 centavos), **LOW**.
- [x] Helper unico `_settlement_reconciliation_severity` em `partners.py`, usado em: reconciliacao por batch, `reconciliation/run` e `top-divergences`.
- [x] Validacao sugerida apos rebuild do servico:
  - `curl -sS "http://localhost:8003/partners/ops/settlements/reconciliation/top-divergences?top_n=5" -H "Authorization: Bearer ${OPS_TOKEN}"`
- [x] Seed SQL controlado (2 HIGH, 2 MEDIUM, 1 LOW): `02_docker/seed_settlement_reconciliation_severity_matrix.sql` (parceiros `OP-ELLAN-001` / `OP-PHARMA-001`, `order_id` ficticios `d0ffee01-...`).
- [x] Limpeza SQL de batches de teste **legados** (nao remove `c0ffee01-*`): `02_docker/cleanup_settlement_reconciliation_legacy_test_batches.sql`.

### 27/04/2026 - Sprint 11 (kickoff): filtro `min_severity` em top divergencias
- [x] Objetivo: painel OPS / comite focar primeiro em risco financeiro (HIGH) ou cortar ruido LOW sem mudar o ranking por `impact_score` dentro do filtro.
- [x] Endpoint estendido:
  - `GET /partners/ops/settlements/reconciliation/top-divergences?min_severity=HIGH|MEDIUM|LOW`
  - Sem parametro: comportamento anterior (todas as severidades).
  - Resposta inclui `min_severity` (null ou valor aplicado), `severity_counts` (totais por severidade na janela, independente de `min_severity`) e `total_divergent_batches` conta apenas divergencias que passam no filtro.
- [x] Validacao HTTP sugerida:
  - `GET .../top-divergences?top_n=10&min_severity=HIGH` (somente HIGH)
  - `GET .../top-divergences?top_n=10&min_severity=MEDIUM` (HIGH + MEDIUM)
  - `GET .../top-divergences?min_severity=LOW` (todas: HIGH, MEDIUM, LOW)
  - `GET .../top-divergences?min_severity=FOO` → `422` com `type=INVALID_MIN_SEVERITY`
- [x] Arquivos alterados:
  - `01_source/order_pickup_service/app/routers/partners.py`
  - `01_source/order_pickup_service/app/schemas/partners.py`
- [x] Reinicio de container necessario nesta rodada? **Sim** (`docker compose up -d --build order_pickup_service`).
### 27/04/2026 - Sprint 11: breakdown por severidade (`severity_counts`)
- [x] Campo `severity_counts` na resposta de `GET /partners/ops/settlements/reconciliation/top-divergences`: objeto com `HIGH`, `MEDIUM`, `LOW` somando todos os batches divergentes na janela (`from`/`to`) e filtro de `partner_id`; **nao** e recortado por `min_severity` (o filtro continua valendo so para `items` e `total_divergent_batches`).
- [x] Arquivos alterados: `partners.py`, `schemas/partners.py`.
- [x] Reinicio de container necessario nesta rodada? **Sim**.

- [x] Backlog opcional Sprint 11:
  - [x] Script SQL de limpeza de batches de teste **legados** (fora da matriz `c0ffee01-*`): `02_docker/cleanup_settlement_reconciliation_legacy_test_batches.sql`
  - [x] Pagina OPS consumindo `top-divergences` + `compare` entregue no Sprint 12 (dashboard operacional de reconciliacao).

### 27/04/2026 - Fechamento formal Sprint 11
- [x] Trilha de reconciliacao executiva entregue e validada em ambiente de lab; sprint marcado como concluido no cabecalho deste documento.
- [x] Artefato de limpeza de dados de demo: `02_docker/cleanup_settlement_reconciliation_legacy_test_batches.sql`.

### 27/04/2026 - Kickoff Sprint 12 — Implantacao (checklist **secao 10**)
- [x] **Contexto**: pedido de "iniciar sprint 10" costuma alinhar ao **capitulo 10** deste ficheiro (`## 10) Checklist de implantacao`), nao ao sprint API **Sprint 10** ja entregue (`top-divergences`, ver registro acima).
- [x] **Objetivo**: transformar o checklist de implantacao em estado rastreavel (evidencias por linha) e identificar buracos reais antes de go-live.
- [x] **Primeira rodada sugerida (hoje)**:
  - confirmar seeds/slots/parceiros em ambiente alvo (marcar linhas 1-2 do checklist com comando ou SELECT);
  - confirmar settlement auditavel (linha 9) com base no que ja existe em OPS;
  - deixar explicito o que falta para carga (linha 5), WCAG (6-7), mensagens (8), dashboard (10).
- [x] Entrega opcional do Sprint 11 executada no Sprint 12: pagina OPS de reconciliacao entregue e expandida.

### 27/04/2026 - Sprint 12: registro **dia 0** (inicio formal + evidencias lab)
- [x] Sprint 12 **iniciado** no repo: checklist §10 passa a ser a fonte de verdade ate novo sprint; kickoff acima marcado como concluido.
- [x] Evidencias em **Postgres** `locker_central` (host local `127.0.0.1:5435`, user `admin`) — *ajustar host se o teu ambiente for outro*:
  - `SELECT COUNT(*) FROM locker_slot_configs` → **40**; `SELECT COUNT(*) FROM locker_slots` → **350** (checklist linha 1).
  - `SELECT COUNT(*) FROM partner_service_areas WHERE is_active IS TRUE` → **7** (checklist linha 2).
  - `SELECT COUNT(*) FROM partner_settlement_batches` → **8**; `SELECT COUNT(*) FROM ops_action_audit WHERE action LIKE 'PARTNER_SETTLEMENT%'` → **11** (checklist linha 9 — geracao + trilha OPS).
- [x] Pendencias de UX/CX do checklist §10 tratadas nesta rodada: WCAG AA, teclado/screen reader e padronizacao de mensagens.

### Quando avisar para reiniciar containers
- [x] Regra aplicada: sempre avisar explicitamente quando houver mudanca de imagem, `docker-compose.yml`, `.env` de servico ou dependencia que exija restart.
- [x] Nesta rodada: como voce reiniciou os containers, refiz as validacoes HTTP ponta a ponta antes de seguir.

### Validacao tecnica desta rodada
- [x] Router/schema compilados sem erro de sintaxe (`py_compile`).
- [x] Endpoints de governanca/KPI validados por HTTP real (`200` e `422`) com token OPS.

### DoD tecnico (reconciliacao OPS / `order_pickup_service`)
- Apos tocar em reconciliacao de settlements (router `partners`, schemas relacionados): **rebuild** do servico (`docker compose -f 02_docker/docker-compose.yml up -d --build order_pickup_service`) e **pytest** `tests/test_settlement_reconciliation_severity.py` (executar a partir de `01_source/order_pickup_service` com o venv do servico).
- Curls e Swagger: token OPS em **`02_docker/.env`** na variavel **`OPS_TOKEN`** (cabecalho `Authorization: Bearer ${OPS_TOKEN}`).

---

## 2) Escopo de entrega

### Incluido
- Seed e saneamento de base para `lockers`, `locker_slot_configs`, `locker_slots`.
- Vinculo parceiro-locker em `ecommerce_partners` + `partner_service_areas`.
- Regras de produto por categoria e capacidade fisica.
- Fluxo de reserva, expiracao e liberacao de estoque.
- Fluxo de notificacao para parceiro com retry e dead-letter.
- Fechamento financeiro mensal por parceiro.

### Fora de escopo imediato
- Predicao de demanda para reposicao automatica.
- Otimizacao de rotas logisticas por ML.
- Replanejamento dinamico de capacidade entre lockers em tempo real.

---

## 3) Premissas de schema (fonte de verdade)

- `products.id` representa SKU e se alinha com `orders.sku_id` e `order_items.sku_id`.
- `product_inventory.quantity_available` ja existe como coluna gerada (`quantity_on_hand - quantity_reserved`).
- `locker_slots.status` controla disponibilidade fisica do compartimento.
- `partner_order_events_outbox.status` suporta `PENDING`, `DELIVERED`, `FAILED`, `DEAD_LETTER`, `SKIPPED`.
- `partner_settlement_batches.status` suporta `DRAFT`, `APPROVED`, `PAID`, `DISPUTED`, `CANCELLED`.
- `inbound_deliveries` e `pickup_tokens` suportam fluxo de armazenagem e retirada.

---

## 4) Principios globais de produto (UX/CX + Acessibilidade + Operacao)

### UX/CX (padrao industria)
- **Fluxo em poucos passos**: cadastro de produto, elegibilidade e pickup com minimo de friccao.
- **Feedback imediato**: toda acao critica retorna status claro (sucesso, bloqueio, proxima acao).
- **Transparencia operacional**: mostrar motivo de rejeicao (dimensao, peso, categoria, SLA) em linguagem objetiva.
- **Confiabilidade percebida**: estados consistentes entre app, locker e notificacoes.
- **Recuperacao de erro**: permitir reprocessamento seguro (idempotencia + retry) sem duplicar alocacao/pickup.

### WCAG AA (obrigatorio)
- Contraste minimo AA em badges, alertas, botoes e estados criticos.
- Navegacao completa por teclado em todas as telas de operacao/pickup.
- Indicacao visual + textual de estado (nao depender apenas de cor).
- Labels e mensagens de erro acessiveis, com foco em leitor de tela.
- Tempo e expiração com aviso antecipado e alternativa de acao.

### Benchmark operacional (Amazon / InPost / Mercado Livre)
- Outbox + retry exponencial para webhooks (confiabilidade de integracao).
- Alocacao concorrente segura com `FOR UPDATE SKIP LOCKED`.
- Journey de pickup simples: identificar -> validar -> abrir -> confirmar -> encerrar.
- Observabilidade de ponta a ponta: evento tecnico + impacto no cliente.
- Operacao orientada a SLA por parceiro, locker e regiao.

---

## 5) Backlog priorizado (P0/P1/P2)

## P0 - Critico (base funcional)

### US-PPL-001 - Fundacao de lockers e slots
**Descricao**: Como operacao, quero lockers e slots materializados para permitir alocacao real.  
**Entrega**:
- Popular `locker_slot_configs` por locker e tamanho.
- Gerar `locker_slots` com `status='AVAILABLE'`.
- Validar consistencia entre `lockers.slots_count` e quantidade de slots gerados.
**Criterios de aceite**:
- 100% dos lockers ativos no recorte do sprint com slots gerados.
- Nenhum locker com slot sem `slot_label` unico por locker.
- Contagem de `locker_slots` por locker >= `slots_available` inicial.
**Prioridade**: P0  
**Status**: Planejado  
**Owner sugerido**: Ops + Backend

### US-PPL-002 - Vinculo parceiro e area de atendimento
**Descricao**: Como parceiro ecommerce, quero estar associado aos lockers permitidos para operar no fluxo.  
**Entrega**:
- Cadastrar parceiros em `ecommerce_partners`.
- Criar regras de cobertura em `partner_service_areas` com `valid_from`, `priority` e `is_active`.
**Criterios de aceite**:
- Parceiro ativo com ao menos 1 area ativa de atendimento.
- Consulta por parceiro retorna apenas lockers ativos e validos na data.
- Regras vencidas (`valid_until`) nao entram na elegibilidade.
**Prioridade**: P0  
**Status**: Planejado  
**Owner sugerido**: Integracoes + Ops

### US-PPL-003 - Catalogo de produto com validacao de elegibilidade
**Descricao**: Como parceiro, quero cadastrar SKU e saber se ele cabe nos lockers da minha area.  
**Entrega**:
- Cadastro em `products` com dimensoes e peso.
- Validacao contra `product_locker_configs` e `locker_slot_configs`.
- Regra de aprovacao para ativacao de SKU com fiscal em `product_fiscal_config`.
**Criterios de aceite**:
- SKU invalido por dimensao/peso retorna bloqueio com motivo.
- SKU aprovado inicia em `DRAFT` e so vai para `ACTIVE` com fiscal minimo valido.
- SKU ativo elegivel em pelo menos 1 combinacao partner + locker + slot_size.
**Prioridade**: P0  
**Status**: Planejado  
**Owner sugerido**: Produtos + Fiscal + Backend

---

## P1 - Alto (fluxo transacional)

### US-PPL-004 - Alocacao atomica de slot
**Descricao**: Como sistema, quero reservar o melhor slot disponivel sem colisao entre requisicoes concorrentes.  
**Entrega**:
- Implementar seletor atomico com `FOR UPDATE SKIP LOCKED`.
- Atualizar `locker_slots.status`, `occupied_since` e referencia de alocacao.
- Registrar trilha em `allocations`.
**Criterios de aceite**:
- Sem dupla alocacao do mesmo slot em concorrencia.
- Alocacao respeita dimensao/peso do produto.
- Em indisponibilidade, retorna erro funcional e nao erro tecnico generico.
**Prioridade**: P1  
**Status**: Planejado  
**Owner sugerido**: Backend

### US-PPL-005 - Inventario, reserva e expiracao
**Descricao**: Como operacao comercial, quero bloquear estoque no checkout e liberar ao expirar para evitar oversell.  
**Entrega**:
- Reserva em `inventory_reservations` no checkout.
- Atualizacao de `product_inventory.quantity_reserved`.
- Worker para expirar reservas e devolver saldo reservado.
**Criterios de aceite**:
- Nao permite reservar quando `quantity_available < quantidade`.
- Reserva expirada altera status para `EXPIRED` e devolve saldo.
- Movimento de inventario rastreavel em `inventory_movements`.
**Prioridade**: P1  
**Status**: Planejado  
**Owner sugerido**: Backend + Dados

### US-PPL-006 - Pickup e liberacao do slot
**Descricao**: Como cliente final, quero retirar meu item com token valido e liberar o compartimento ao concluir.  
**Entrega**:
- Validacao de token em `pickup_tokens`.
- Atualizacao de estado de entrega (`inbound_deliveries`) ou pedido/pickup equivalente.
- Liberacao de slot em `locker_slots` apos retirada confirmada.
**Criterios de aceite**:
- Token expirado/invalido bloqueia retirada com resposta funcional.
- Pickup concluido atualiza timestamps de retirada.
- Slot volta para `AVAILABLE` apos encerramento do ciclo.
**Prioridade**: P1  
**Status**: Planejado  
**Owner sugerido**: Backend + Hardware Integration

---

## P2 - Medio prazo (confiabilidade e financeiro)

### US-PPL-007 - Entrega de eventos para parceiro (outbox)
**Descricao**: Como parceiro, quero receber eventos de pedido/entrega com confiabilidade e reprocessamento controlado.  
**Entrega**:
- Worker do `partner_order_events_outbox` com lock concorrente e retry.
- Entrega para `partner_webhook_endpoints`.
- Controle de tentativa, erro e dead-letter.
**Criterios de aceite**:
- Eventos `PENDING` sao processados respeitando `next_retry_at`.
- Evento 2xx vira `DELIVERED`; falhas repetidas viram `DEAD_LETTER`.
- Taxa de entrega e backlog monitoraveis.
**Prioridade**: P2  
**Status**: Planejado  
**Owner sugerido**: Integracoes + Plataforma

### US-PPL-008 - Settlement mensal de parceiros
**Descricao**: Como financeiro, quero consolidar pedidos do periodo e fechar repasse por parceiro.  
**Entrega**:
- Geracao de `partner_settlement_batches` por periodo.
- Consolidacao de itens em `partner_settlement_items`.
- Fluxo de aprovacao e pagamento do lote.
**Criterios de aceite**:
- Batch mensal com `gross_revenue_cents`, `revenue_share_pct` e `net_amount_cents` consistentes.
- Mudanca de status controlada (`DRAFT` -> `APPROVED` -> `PAID`).
- Rastreabilidade de lote e referencia de settlement.
**Prioridade**: P2  
**Status**: Planejado  
**Owner sugerido**: Financeiro + Backend

---

## 6) Planejamento por sprint (8 sprints)

### Sprint 0 - Base e seeds (1 semana)
- US-PPL-001, US-PPL-002
- Saida: base de lockers/slots e cobertura de parceiros prontas.
- Gate UX/CX + WCAG AA:
  - checklist de acessibilidade da board e estados de operacao aprovado.
  - nomenclatura de status padronizada para leitura humana e tecnica.

### Sprint 1 - Catalogo e elegibilidade (2 semanas)
- US-PPL-003
- Saida: parceiros conseguem cadastrar SKU e validar elegibilidade.
- Gate UX/CX + WCAG AA:
  - mensagem de erro de elegibilidade com causa exata e sugestao de ajuste.
  - formulario de cadastro com validacao em tempo real e foco acessivel.

### Sprint 2 - Alocacao concorrente (2 semanas)
- US-PPL-004
- Saida: engine de alocacao atomica operacional.
- Gate UX/CX + WCAG AA:
  - status de alocacao exibido com texto + cor + icone.
  - fallback de indisponibilidade com proxima melhor opcao sugerida.

### Sprint 3 - Inventario e reservas (2 semanas)
- US-PPL-005
- Saida: fluxo de reserva/expiracao com antiover sell.
- Gate UX/CX + WCAG AA:
  - alertas de baixo estoque com prioridade clara e acao em 1 clique.
  - tela de inventario com navegacao por teclado e leitura por screen reader.

### Sprint 4 - Pickup e ciclo fisico (1 semana)
- US-PPL-006
- Saida: retirada completa com liberacao de slot.
- Gate UX/CX + WCAG AA:
  - fluxo de pickup no maximo 3 interacoes principais.
  - instrucoes de pickup com linguagem simples e alto contraste.

### Sprint 5 - Outbox e webhooks (1.5 semana)
- US-PPL-007
- Saida: eventos confiaveis para parceiros.
- Gate UX/CX + WCAG AA:
  - painel de reentrega/dead-letter com priorizacao por impacto no cliente.
  - feedback de envio com status legivel e exportavel para operacao.

### Sprint 6 - Settlement (1 semana)
- US-PPL-008
- Saida: fechamento financeiro mensal operacional.
- Gate UX/CX + WCAG AA:
  - visao de lote clara para financeiro (gross/share/net) sem ambiguidade.
  - labels e tabelas com contraste AA e sem dependencia exclusiva de cor.

### Sprint 7 - Integracao e hardening (1 semana)
- Testes de carga, caos e regressao ponta a ponta.
- Saida: readiness para producao.
- Gate UX/CX + WCAG AA:
  - bateria final de acessibilidade AA e jornada completa de cliente/operador.
  - simulacao de incidentes com runbook acionavel.

---

## 7) KPIs oficiais de acompanhamento

### Catalogo e elegibilidade
- SKUs criados por parceiro
- % de SKUs aprovados (DRAFT -> ACTIVE)
- % de bloqueios por regra de dimensao/peso/categoria

### Operacao fisica de lockers
- Taxa de ocupacao por locker e slot_size
- Taxa de falha de alocacao
- Tempo medio de alocacao

### Inventario
- `quantity_available` medio por SKU/locker
- Taxa de reserva expirada
- Incidencia de tentativa de oversell bloqueada

### Integracao de parceiros
- Taxa de entrega de webhook (2xx)
- Tempo medio ate `DELIVERED`
- Backlog `PENDING` e `DEAD_LETTER`

### Financeiro
- Valor bruto e liquido por parceiro no mes
- % de batches pagos dentro do prazo
- Divergencia entre batch e itens conciliados

---

## 8) KPIs de UX/CX e Acessibilidade

### Experiencia do parceiro e operacao
- Tempo medio para cadastrar SKU ate `ACTIVE`
- Taxa de erro por etapa da jornada (cadastro, alocacao, pickup)
- Tempo medio de resolucao de bloqueios operacionais
- Taxa de reprocessamento sem intervencao manual

### Experiencia do cliente final
- Tempo medio de pickup (inicio -> porta aberta -> conclusao)
- Taxa de pickup concluido na primeira tentativa
- Taxa de expiracao por falha de comunicacao/ux
- NPS/CSAT por jornada de retirada (quando disponivel)

### Acessibilidade (WCAG AA)
- % de telas criticas com contraste AA validado
- % de fluxos operaveis 100% por teclado
- % de componentes com semantica acessivel e mensagens claras
- Incidentes de acessibilidade reportados por sprint

---

## 9) Riscos e mitigacoes

- **Risco**: divergencia de id/tipo entre tabelas legadas (`varchar(36)` vs `varchar` amplo).  
  **Mitigacao**: padronizar validadores de ID no servico antes de persistir.

- **Risco**: alocacao concorrente gerar starvation em lockers com alta disputa.  
  **Mitigacao**: ordenacao estavel + telemetria de tentativas/falhas por locker.

- **Risco**: regras de elegibilidade muito restritivas derrubarem conversao.  
  **Mitigacao**: monitorar motivos de rejeicao e ajustar `product_locker_configs` com governanca.

- **Risco**: webhook com indisponibilidade recorrente de parceiro.  
  **Mitigacao**: retry com backoff + `DEAD_LETTER` + alerta operacional.

---

## 10) Checklist de implantacao

> **Sprint 12:** marcar cada linha abaixo com evidencia; kickoff em `### 27/04/2026 - Kickoff Sprint 12`; dia 0 em `### 27/04/2026 - Sprint 12: registro dia 0`.

- [x] Seeds de `locker_slot_configs` e `locker_slots` executados e validados.
  - Evidencia dia 0: **40** configs, **350** slots (ver registro Sprint 12 dia 0).
- [x] Parceiros ativos com cobertura em `partner_service_areas`.
  - Evidencia dia 0: **7** linhas `is_active=true` em `partner_service_areas`.
- [x] Cadastro e aprovacao de SKU funcionando com fiscal minimo.
  - Evidencia Sprint 12: `POST /partners/OP-ELLAN-001/products` com `metadata_json` fiscal (`fiscal_ncm`, `fiscal_cest`, `fiscal_cfop`) para `product_id=s12-sku-fiscal-1777369676` retornou `status=DRAFT`, `eligibility_ok=true`; em seguida `PATCH /products/s12-sku-fiscal-1777369676/status` com `to_status=ACTIVE` retornou `from_status=DRAFT` e `to_status=ACTIVE`.
- [x] Alocacao concorrente validada com teste de carga.
  - Evidencia Sprint 12 (carga concorrente em `POST /partners/OP-ELLAN-001/lockers/SP-ALPHAVILLE-SHOP-LK-001/slot-allocations/pick`, 30 requisicoes, 15 workers, produto `s12-sku-fiscal-1777369676`): `200=16`, `409=14`, `other=0`, `detail.type=SLOT_NOT_AVAILABLE` para as falhas esperadas por esgotamento de slot; latencia `p50=416.22ms`, `p95=547.27ms`, tempo total `667.87ms`.
  - Pos-teste (higiene de ambiente): limpeza de `current_allocation_id LIKE 's12load-%'` em `locker_slots`; validacao final `COUNT(*)=0`.
- [x] Reserva/expiracao de inventario validada sem oversell.
  - Evidencia Sprint 12 (fluxo endpoint): `POST /inventory/reserve` reservando **17** unidades de `cookie_laranja` em `SP-OSASCO-CENTRO-LK-001` (`slot_size=M`) retornou `ok=true` e `quantity_available=0`; segunda tentativa `POST /inventory/reserve` para mais **1** unidade retornou **409** com `type=INSUFFICIENT_INVENTORY` (`available=0`, `requested=1`), provando bloqueio de oversell; limpeza executada com `POST /inventory/reservations/{reservation_id}/release` (`status=RELEASED`, `quantity_available=17`).
- [x] Pickup libera slot e fecha ciclo corretamente.
  - Evidencia Sprint 12: `POST /partners/OP-ELLAN-001/lockers/SP-ALPHAVILLE-SHOP-LK-001/slot-allocations/al_be926b42910f4b08a3604f48dae37142/pickup-confirm` retornou `ok=true`, `idempotent=false`, `allocation_state=PICKED_UP`, `order_status=PICKED_UP`, `pickup_status=REDEEMED`, `slot_label=P-001`; replay do mesmo endpoint retornou `ok=true`, `idempotent=true` (idempotencia confirmada).
- [x] Outbox com retry/dead-letter monitorado.
  - Evidencia Sprint 12: `GET /ops/integration/order-events-outbox?limit=5` retornou `ok=true`, `total=22`; `GET /ops/integration/order-events-outbox/dead-letter-priority?limit=5` retornou `ok=true`, `total_dead_letters=10`, `total_groups=5` (com `Authorization: Bearer ${OPS_TOKEN}`).
- [x] Settlement mensal gerado e auditavel.
  - Evidencia dia 0: **8** batches em `partner_settlement_batches`; **11** linhas de auditoria `PARTNER_SETTLEMENT%` em `ops_action_audit` + endpoints OPS de reconciliacao (sprints anteriores).
- [x] Contraste e componentes criticos validados em WCAG AA.
  - Evidencia Sprint 12: dashboard adota texto + cor para severidade (chips `H/M/L` + barra), labels visiveis (`Presets de janela`, `Grade`) e estado ativo explicito (`Janela ativa`), evitando comunicacao apenas por cor.
- [x] Fluxos principais testados com teclado e leitor de tela.
  - Evidencia Sprint 12: controles interativos em elementos nativos (`button`, `details/summary`, `input`, `select`) com foco navegavel por TAB; heatmap recebeu `aria-label` por celula e descricao operacional do clique/filtro.
- [x] Mensagens de erro padronizadas com causa e acao recomendada.
  - Evidencia Sprint 12: parser unico de erro no dashboard (`parseError`) com fallback consistente; mensagens de copia/runbook e falha orientam proxima acao (ex.: "Copie manualmente..." e instrucoes de filtro/limpar selecao no heatmap).
- [x] Dashboard operacional com priorizacao de incidentes por impacto no cliente.
  - Evidencia Sprint 12: pagina frontend em `01_source/frontend/src/pages/OpsPartnersReconciliationDashboardPage.jsx`, rota `GET /ops/partners/reconciliation-dashboard` no `App.jsx`, consumindo `GET /partners/ops/settlements/reconciliation/top-divergences` e `GET /partners/ops/settlements/reconciliation/compare`, com filtros `partner_id`, `from`, `to`, `min_severity`, `top_n`, presets `1h/6h/24h/7d/30d`, Inbound colapsavel com runbook (abrir/copiar), grade `Simplificada/Completa`, grafico de tendencia, severidade H/M/L no tempo, correlacao taxa vs batches (s12.5), heatmap HIGH clicavel com filtro automatico por janela.

### 28/04/2026 - Backlog Sprint 13 (priorizacao avancada global)
- [ ] **Priorizacao avancada (scatter)**: `impact_score` vs recencia (bolha por severidade) no dashboard OPS de reconciliacao.
- **Justificativa para adiar no Sprint 12 (registro de decisao)**:
  - foco do inbound em leitura de **30 segundos**: trend + H/M/L no tempo entregam estado e direcao com menor carga cognitiva;
  - semantica de `recencia` ainda precisa governanca global (ex.: `created_at` vs `updated_at` vs `reconciled_at`) para evitar ruido de interpretacao entre regioes;
  - risco de falsa priorizacao sem normalizacao de escala/cluster (bolhas grandes podem mascarar recorrencia de medio impacto);
  - custo adicional de UX/WCAG para padrao mundial (nao depender apenas de cor, navegacao por teclado, leitura por screen reader) e maior risco de regressao visual no curto prazo;
  - valor incremental menor para MTTR imediato frente aos dois graficos de Sprint 12.
- **Criterios de aceite (padrao global ELLAN LAB)**:
  - definicao formal e documentada de `recencia` e timezone padrao para todas as operacoes;
  - legenda explicita + modo acessivel sem dependencia exclusiva de cor para severidade;
  - navegacao por teclado e leitura por screen reader validada no componente;
  - tooltips com contexto operacional minimo (batch, partner, impact_score, idade do evento, severidade);
  - validacao de interpretacao com time de operacao: acerto de priorizacao em cenarios de teste controlados;
  - medicao de uso/resultado apos rollout (tempo de triagem e taxa de escalonamento correto).

---

## 11) Padrao de decisao de UX/CX por historia (Definition of Done expandido)

Para cada US do backlog, considerar concluido apenas quando:
- Regra funcional validada em banco/API.
- Jornada do usuario testada (parceiro, operador ou cliente final).
- Estados criticos comunicados de forma clara, sem ambiguidade.
- Checklist WCAG AA do fluxo aprovado.
- Evidencia operacional registrada (log, dashboard, ou print de fluxo).

---

## 12) Proxima revisao

Data sugerida: 7 dias apos inicio do Sprint 0.  
Objetivo da revisao: confirmar base operacional pronta, aderencia a UX/CX e conformidade WCAG AA para entrada no Sprint 1.