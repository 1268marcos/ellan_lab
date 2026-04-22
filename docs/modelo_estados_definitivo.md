# Modelo de Estados Definitivo - V2 Canonico

## Principio central
Nunca usar um unico status para representar tres verdades diferentes.

### As tres verdades separadas (persistidas)
1. `machine_state` -> O que a maquina fez (hardware/runtime)
2. `pickup_phase` -> O que o caso de uso de retirada fez
3. `evidence_score` -> Quao forte e a prova da retirada real

### Regra de ouro
"Retirado comprovado" so existe com evidencia forte (`evidence_score >= 80`).

---

## V2 canonico (fonte de verdade)

### Eixos canonicos no banco
- `machine_state` (telemetria operacional)
- `pickup_phase` (progresso do fluxo)
- `evidence_score` (`0..100`)
- `dispute_state` (ciclo de disputa, separado do fluxo principal)

### Campos derivados (nao editar manualmente)
- `evidence_strength` derivado de `evidence_score`
- `order_status` derivado de pagamento + `pickup_phase` + `evidence_score` + `dispute_state`

> Se `order_status` for persistido por performance, deve ser atualizado apenas por projecao controlada (trigger/job), nunca por API de negocio.

---

## Enums V2

### `machine_state` (hardware/runtime)
| Enum | Significado |
|------|-------------|
| UNKNOWN | Telemetria insuficiente |
| IDLE | Sem operacao ativa |
| PAID_PENDING_PICKUP | Pago e pronto no equipamento |
| DISPENSE_TRIGGERED | Comando de liberacao emitido |
| OPENING | Transicao de abertura |
| OPEN | Porta aberta |
| CLOSING | Transicao de fechamento |
| CLOSED_AFTER_OPEN | Fechou apos ciclo |
| RELEASED | Alocacao liberada |
| OUT_OF_STOCK | Sem item disponivel |
| ERROR | Falha operacional |
| MAINTENANCE | Sob manutencao |

### `pickup_phase` (caso de uso)
| Enum | Significado |
|------|-------------|
| CREATED | Pickup criado |
| READY_FOR_PICKUP | Pronto para retirada |
| AUTH_PENDING | Aguardando credencial |
| AUTHENTICATED | Credencial validada |
| DISPENSE_REQUESTED | Comando enviado |
| ACCESS_GRANTED | Acesso liberado |
| IN_PROGRESS | Retirada em andamento |
| COMPLETED_UNVERIFIED | Concluido sem prova forte |
| COMPLETED_VERIFIED | Concluido com prova forte |
| EXPIRED | Prazo vencido |
| CANCELLED | Cancelado |
| FAILED | Erro no fluxo |
| RECONCILING | Em reconcilicao |
| RECONCILED | Caso reconciliado |

### `dispute_state` (separado de pickup)
| Enum | Significado |
|------|-------------|
| NONE | Sem disputa |
| OPEN | Disputa aberta |
| UNDER_REVIEW | Em analise |
| ACCEPTED | Disputa procedente |
| REJECTED | Disputa improcedente |
| CLOSED | Encerrada |

### `evidence_strength` (derivado de score)
| Enum | Faixa |
|------|-------|
| NONE | 0 |
| WEAK | 1..39 |
| MEDIUM | 40..79 |
| STRONG | 80..99 |
| FINAL | 100 |

---

## Invariantes obrigatorias

1. `pickup_phase = COMPLETED_VERIFIED` exige `evidence_score >= 80` e `verified_at IS NOT NULL`
2. `pickup_phase = COMPLETED_UNVERIFIED` exige `COALESCE(evidence_score, 0) < 80`
3. `dispute_state <> NONE` exige `disputed_at IS NOT NULL`
4. `pickup_phase = RECONCILED` exige `reconciled_at IS NOT NULL`
5. `order_status` e derivado, nao atualizavel diretamente por API

---

## Transicoes permitidas (`pickup_phase`)

- `CREATED -> READY_FOR_PICKUP | CANCELLED | FAILED`
- `READY_FOR_PICKUP -> AUTH_PENDING | EXPIRED | CANCELLED`
- `AUTH_PENDING -> AUTHENTICATED | FAILED | EXPIRED`
- `AUTHENTICATED -> DISPENSE_REQUESTED | FAILED`
- `DISPENSE_REQUESTED -> ACCESS_GRANTED | FAILED`
- `ACCESS_GRANTED -> IN_PROGRESS | FAILED`
- `IN_PROGRESS -> COMPLETED_UNVERIFIED | COMPLETED_VERIFIED | FAILED`
- `COMPLETED_UNVERIFIED -> RECONCILING`
- `RECONCILING -> RECONCILED | COMPLETED_VERIFIED | FAILED`
- Estados terminais: `COMPLETED_VERIFIED`, `RECONCILED`, `EXPIRED`, `CANCELLED`, `FAILED`

---

## SQL recomendado (V2)
```sql
-- Tipos fortes para evitar valores invalidos
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pickup_phase') THEN
    CREATE TYPE pickup_phase AS ENUM (
      'CREATED','READY_FOR_PICKUP','AUTH_PENDING','AUTHENTICATED',
      'DISPENSE_REQUESTED','ACCESS_GRANTED','IN_PROGRESS',
      'COMPLETED_UNVERIFIED','COMPLETED_VERIFIED',
      'EXPIRED','CANCELLED','FAILED','RECONCILING','RECONCILED'
    );
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dispute_state') THEN
    CREATE TYPE dispute_state AS ENUM (
      'NONE','OPEN','UNDER_REVIEW','ACCEPTED','REJECTED','CLOSED'
    );
  END IF;
END $$;

ALTER TABLE public.pickups
  ADD COLUMN IF NOT EXISTS machine_state varchar(50),
  ADD COLUMN IF NOT EXISTS pickup_phase pickup_phase,
  ADD COLUMN IF NOT EXISTS evidence_score integer,
  ADD COLUMN IF NOT EXISTS dispute_state dispute_state DEFAULT 'NONE',
  ADD COLUMN IF NOT EXISTS verified_at timestamptz,
  ADD COLUMN IF NOT EXISTS disputed_at timestamptz,
  ADD COLUMN IF NOT EXISTS reconciled_at timestamptz,
  ADD COLUMN IF NOT EXISTS aggregate_version bigint NOT NULL DEFAULT 0;

ALTER TABLE public.pickups
  DROP CONSTRAINT IF EXISTS ck_pickups_evidence_score_range,
  ADD CONSTRAINT ck_pickups_evidence_score_range
  CHECK (evidence_score IS NULL OR evidence_score BETWEEN 0 AND 100);

ALTER TABLE public.pickups
  ADD CONSTRAINT ck_pickups_verified_requires_strong_evidence
  CHECK (
    pickup_phase <> 'COMPLETED_VERIFIED'
    OR (evidence_score >= 80 AND verified_at IS NOT NULL)
  );

ALTER TABLE public.pickups
  ADD CONSTRAINT ck_pickups_unverified_requires_weak_evidence
  CHECK (
    pickup_phase <> 'COMPLETED_UNVERIFIED'
    OR COALESCE(evidence_score, 0) < 80
  );

ALTER TABLE public.pickups
  ADD CONSTRAINT ck_pickups_dispute_requires_disputed_at
  CHECK (
    dispute_state = 'NONE' OR disputed_at IS NOT NULL
  );
```

---

## Auditoria append-only (obrigatoria)

Criar trilha de eventos imutavel para antifraude e investigacao:

- Tabela sugerida: `pickup_events`
- Campos minimos:
  - `id`
  - `pickup_id`
  - `version` (sequencial por pickup)
  - `event_type`
  - `payload` (jsonb)
  - `source`
  - `occurred_at`
  - `idempotency_key`
- Constraints:
  - `UNIQUE (pickup_id, version)`
  - `UNIQUE (pickup_id, idempotency_key)` (ou global, conforme arquitetura)

Fluxo de escrita:
1. validar transicao
2. incrementar `version`
3. gravar evento
4. atualizar snapshot em `pickups`

---

## Secao de migracao: modelo atual -> V2 canonico

### 1) Compatibilidade inicial (sem quebra)
- Adicionar novas colunas (`pickup_phase`, `dispute_state`) sem remover antigas.
- Manter leitura dos campos antigos durante transicao.
- Comecar a preencher novos campos em paralelo (dual-write controlado).

### 2) Mapeamento de estados antigos para novos

#### `pickup_state` antigo -> `pickup_phase` novo
- `AUTHENTICATION_PENDING` -> `AUTH_PENDING`
- `COLLECTION_IN_PROGRESS` -> `IN_PROGRESS`
- Demais estados equivalentes com mesmo nome
- `DISPUTED` (antigo) sai de `pickup_phase` e passa para `dispute_state = OPEN`

#### `evidence_state` antigo -> `evidence_score` inicial sugerido
- `NONE` -> `0`
- `CODE_VALIDATED` / `QR_VALIDATED` -> `20`
- `DOOR_OPENED` / `DOOR_CLOSED` -> `50`
- `ITEM_REMOVAL_SIGNAL` -> `70`
- `WEIGHT_DELTA_CONFIRMED` / `IR_BEAM_CONFIRMED` -> `85`
- `IMAGE_CONFIRMED` / `VIDEO_CONFIRMED` / `OPERATOR_CONFIRMED` -> `90`
- `MULTI_SIGNAL_CONFIRMED` -> `100`
- `REJECTED` -> manter score atual e marcar para revisao manual
- `DISPUTED` -> mover para `dispute_state = OPEN`

> Observacao: este mapeamento e bootstrap. A regra final deve ser baseada em eventos/sinais, nao apenas no estado agregado legado.

### 3) Derivacao de `evidence_strength`
- Implementar funcao deterministica por faixa:
  - `0` -> `NONE`
  - `1..39` -> `WEAK`
  - `40..79` -> `MEDIUM`
  - `80..99` -> `STRONG`
  - `100` -> `FINAL`

### 4) Endurecimento progressivo
- Fase A: criar colunas e popular historico
- Fase B: ativar escrita principal no V2
- Fase C: ativar constraints de invariantes
- Fase D: tornar campos legados somente leitura
- Fase E: remover campos legados apos janela de seguranca

### 5) Cutover recomendado
- Definir janela de freeze de deploy para transicao de escrita
- Rodar backfill com auditoria de contagem por estado
- Validar divergencia entre legado e V2 (amostras e totalizadores)
- Ativar alertas para transicao invalida e regressao de score

---

## Estado atual da implantacao (22/04/2026)

### O que ja foi aplicado
- `001_add_v2_columns.sql`
- `002_backfill_v2.sql`
- `003_add_constraints.sql`
- `004_lock_legacy_write_paths.sql`

### Validacao pos-migracao (resultado real)
- `total_pickups = 108`
- `total_inconsistencias_v2 = 0`
- `pickups_sem_eventos = 0`
- `pickups_com_eventos = 108`
- Scripts detalhados de inconsistencias/divergencias sem retorno de linhas

### Incidente operacional observado apos cutover
- Worker `order_lifecycle_pickup_worker` falhando no release runtime com:
  - `NameResolutionError: Failed to resolve 'runtime'`
  - endpoint tentado: `http://runtime:8200/locker/slots/{slot}/set-state`
- Impacto: timeout de pickup executa parte interna, mas falha em efeito externo de liberacao no runtime.

### Segundo incidente observado na estabilizacao
- `order_pickup_service` nao sobe por erro de import:
  - `ModuleNotFoundError: No module named 'app.db'`
  - origem: `app/services/pickup_completion_service.py` importando `from app.db.session import SessionLocal`
- Impacto:
  - API indisponivel durante bootstrap
  - `order_pickup_domain_event_worker` sem processamento efetivo por dependencia do service principal

### Terceiro incidente observado na estabilizacao
- Erro de escrita em `pickups` durante fluxo legado:
  - `CheckViolation: ck_pickups_v2_evidence_score_range`
  - contexto: `INSERT` legado nao preenchia colunas V2 (`evidence_score`)
- Impacto:
  - falha de flush/commit
  - `PendingRollbackError` em cascata na mesma sessao SQLAlchemy

### Quarto incidente observado na estabilizacao (KIOSK PT)
- Erro funcional em criacao de pedido KIOSK PT:
  - retorno `INVALID_PAYMENT_METHOD`
  - `allowed` retornava lista antiga (`pix`, `creditCard`, `debitCard`, `giftCard`)
  - mesmo com locker PT exibindo metodos permitidos (`apple_pay`, `mbway`, etc)
- Impacto:
  - bloqueio indevido de metodos validos no frontend operacional
  - pedido KIOSK PT falhando com `400 Bad Request`

### Quinto incidente observado na estabilizacao (KIOSK PT com Apple Pay)
- Erro em criacao de pedido KIOSK PT com `apple_pay`:
  - `KIOSK_CREATE_ORDER_FAILED`
  - causa raiz: `_resolve_instruction_type` nao suportava `apple_pay`
- Efeito colateral:
  - quando erro ocorria apos `locker_allocate`, a gaveta podia permanecer `RESERVED` no runtime
  - risco de slot preso ate timeout/reprocessamento

### Regra funcional consolidada (KIOSK e identidade)
- Pedido criado via canal `KIOSK` deve ser sempre anonimo:
  - `orders.user_id` deve permanecer `NULL`
  - mesmo que o operador esteja autenticado no painel web
- Identificacao no passo de comprovante e apenas de contato:
  - `receipt_email` e/ou `receipt_phone`
  - sem vinculo de titularidade do pedido ao usuario autenticado

### Causa raiz
- `order_lifecycle_pickup_worker` (e stack de lifecycle) sem `LOCKER_RUNTIME_INTERNAL` no `docker-compose`.
- `RuntimeClient` do lifecycle com fallback legado para `http://runtime:8200`.
- Token interno do cliente runtime dependia de `INTERNAL_SERVICE_TOKEN`/`X_INTERNAL_TOKEN` e nao lia `INTERNAL_TOKEN`.

### Correcao aplicada
- `02_docker/docker-compose.yml`
  - adicionado `LOCKER_RUNTIME_INTERNAL=http://backend_runtime:8000`
  - adicionado `INTERNAL_SERVICE_TOKEN=${ORDER_INTERNAL_TOKEN}`
  - aplicado em:
    - `order_lifecycle_service`
    - `order_lifecycle_worker`
    - `order_lifecycle_pickup_worker`
- `01_source/backend/order_lifecycle_service/app/clients/runtime_client.py`
  - fallback de base URL atualizado para `http://backend_runtime:8000`
  - fallback de token atualizado para incluir `INTERNAL_TOKEN`
- `01_source/order_pickup_service/app/services/pickup_completion_service.py`
  - import corrigido para `from app.core.db import SessionLocal`
  - rotina normalizada para compatibilidade com modelo atual (legado + V2 quando campos existirem)
  - remocao de referencia a atributo inexistente de allocation (`released_at`)
- `01_source/order_pickup_service/app/jobs/lifecycle_events_consumer.py`
  - `pickup.door_closed` passa a marcar `handled=True` e fazer `ack` do evento apos sucesso
- `03_data/scripts_sql/hotfix/005_fix_pickups_v2_defaults_for_legacy_inserts.sql`
  - define defaults de compatibilidade:
    - `evidence_score DEFAULT 0`
    - `evidence_strength DEFAULT 'NONE'`
    - `dispute_state DEFAULT 'NONE'`
  - backfill de nulos existentes
  - reforca trigger V2 para autocorrigir inserts legados (`evidence_score := COALESCE(..., 0)`)
- `01_source/order_pickup_service/app/routers/kiosk.py`
  - validacao do metodo/interface no `POST /kiosk/orders` passou a usar `validate_locker_for_order` (source of truth do locker real)
  - remove dependencia de bloqueio por `capability profile` desatualizado para esse fluxo
  - efeito esperado: PT aceitar `apple_pay` / `mbway` quando permitidos no locker selecionado
- `01_source/order_pickup_service/app/services/pickup_payment_fulfillment_service.py`
  - `_resolve_instruction_type` ampliado para metodos globais (incluindo `apple_pay`, `google_pay`, `mbway`, `multibanco_reference`)
  - adicionado cleanup defensivo no erro de criacao KIOSK:
    - `db.rollback()`
    - tentativa de `locker_release` no runtime quando allocation ja tiver sido criada
  - efeito esperado:
    - `apple_pay` nao falhar por metodo "unsupported"
    - erro intermediario nao deixar slot preso em `RESERVED`
- `01_source/order_pickup_service/app/services/pickup_payment_fulfillment_service.py`
  - criacao de pedido KIOSK forca `user_id=None` e `guest_session_id=None`
- `01_source/order_pickup_service/app/routers/kiosk.py`
  - `kiosk_identify` forca `order.user_id=None` para canal `KIOSK`
  - `_finalize_kiosk_payment` e `kiosk_payment_simulate_approved` aplicam blindagem extra para manter anonimato

### Runbook rapido apos deploy dessa correcao
1. Recriar containers lifecycle:
   - `docker compose up -d --build order_lifecycle_service order_lifecycle_worker order_lifecycle_pickup_worker`
2. Confirmar env no container do pickup worker:
   - `docker compose exec order_lifecycle_pickup_worker env | grep -E "LOCKER_RUNTIME_INTERNAL|INTERNAL_SERVICE_TOKEN|INTERNAL_TOKEN"`
3. Validar logs:
   - sem novas ocorrencias de `Failed to resolve 'runtime'`
   - presenca de passos `runtime_set_state_ok` e/ou `runtime_release_ok`
4. Reexecutar validacao V2:
   - `20260422_select_001_validacao_v2_resumo.sql`
   - `20260422_select_002_validacao_v2_inconsistencias_detalhes.sql`
   - `20260422_select_003_validacao_v2_divergencia_legacy_vs_v2.sql`
5. Confirmar startup dos servicos criticos:
   - `docker compose logs order_pickup_service --tail=100`
   - `docker compose logs order_pickup_domain_event_worker --tail=100`
   - esperado: sem `ModuleNotFoundError: No module named 'app.db'`
6. Confirmar integridade de escrita em pickup legado:
   - esperado: sem `CheckViolation: ck_pickups_v2_evidence_score_range`
   - esperado: sem `PendingRollbackError` em cascata por violacao anterior

---

## Modelo legado (V1)

O desenho anterior fica oficialmente classificado como legado, com coexistencia temporaria apenas durante migracao.