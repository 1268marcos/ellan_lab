# Gaps de entrega — `docs/` vs `01_source/` (foco LOCKERS)

**Data:** 2026-05-07  
**Audiência:** DEV / Eng. Software (lockers, pickup, runtime)  
**Objetivo:** Lista única do que evoluir em **código**, testes e documentação para fechar a distância entre o que está escrito em `docs/` e o que o monorepo entrega hoje.

> **Legado abandonado:** `backend_sp` e `backend_pt` foram o desenho inicial regional; **não existem** em `01_source/` e **não devem** ser referenciados em código, proxies ou documentação nova. O dono da gaveta é **`01_source/backend/runtime/`**.

---

## 1. Resumo executivo

| Área | Situação | Risco para entrega |
|------|----------|-------------------|
| **Cadeia locker (allocate → pay → commit → pickup)** | Implementada em `backend/runtime` + `payment_gateway` + `order_pickup_service` + `order_lifecycle` | **Médio** — E2E shell existe; **sem testes unitários** em runtime/lifecycle |
| **Documentação de arquitetura** | Ainda descreve `backend_sp` / `backend_pt` e portas 8201/8202 | **Alto** — onboarding e intervenção no locker errados |
| **Portas / proxies (dev)** | Compose usa pickup **8003**; docs COO e Vite default **8002**; `/api/runtime` no FE aponta para **partner** (8402), não runtime (**8200**) | **Alto** — dashboards NOC/campo quebram em dev |
| **Portal COO** | API rica no pickup; UI só dashboard real + 11 placeholders | **Médio** — “portal entregue” na doc ≠ UX completa |
| **NOC / SIMT** | Dois backends (runtime stub + lifecycle agregado); FE mistura :8200 e :8010 | **Alto** — métricas de rede locker não confiáveis no MVP runtime |
| **Microserviços “visão”** | `catalog`, `inventory`, `wallet`, `logistics` existem em código, **fora** do `docker-compose.yml` principal | **Médio** — sprint docs dizem “concluído” mas orquestração lab incompleta |
| **Frontend v0 → v1** | Checkout/kiosk/fiscal pesado no **v0**; hub **v1** com COO/CEO/ops | **Alto** — regressão 12/12 não cobre migração de fluxo público |
| **Fiscal / FA5** | Serviço + testes fortes; Grafana/Metabase no compose | **Baixo** para locker core; relevante para go-live financeiro |

**Conclusão:** O núcleo **físico-digital do locker** está no lugar certo (`01_source/backend/runtime`). O maior gap de entrega não é “falta de backend locker”, e sim **inconsistência documental**, **proxies/portas**, **UI incompleta (COO/NOC)** e **ausência de testes automatizados** nos serviços que libertam/fecham gavetas.

---

## 2. Mapa de verdade (locker-first)

Use esta tabela como fonte única em code review e planeamento — não os PDFs/HTML antigos de SP/PT.

| Responsabilidade | Código canónico | Porta típica (compose / dev) | Docs que ainda erram |
|------------------|-----------------|------------------------------|----------------------|
| Gaveta / slot / MQTT / allocate-commit | `01_source/backend/runtime/` | **8200** (host) → container 8000 | `docs/architecture/*`, `HANDOFF.md`, `ROADMAP.md` → `backend_sp/pt` |
| Pedido, pagamento confirmado, pickup, QR, kiosk | `01_source/order_pickup_service/` | **8003** (compose) / **8002** (uvicorn local, mapeado 8402 no partner) | COO API doc, `e2e_coo_smoke.sh`, Vite `ORDER_PICKUP_SERVICE_PROXY` default **8002** |
| Deadlines, eventos, NOC agregado DB | `01_source/backend/order_lifecycle_service/` | **8010** | Runbook NOC só cita runtime |
| Pagamento → runtime | `01_source/payment_gateway/` | **8000** | OK em `E2E_PAYMENT_MINIMAL_STACK_DESIGN.md` |
| Auth parceiro BFF | `01_source/partner_service/` | **8402** → processo **8002** | Confundido com runtime no proxy FE |
| Portal COO (API) | `order_pickup_service/app/routers/coo/` | via pickup (8003) | OK em `docs/api/coo-portal-api.md` |
| Portal COO (UI) | `01_source/frontend/src/pages/coo/` | Vite **5173** ou **5180** | Runbook 5180 OK; nginx 5180 é outro stack |
| CEO (UI + API) | `frontend/.../CeoDashboard.tsx` + `executive_dashboard.py` | pickup + hub v1 | Pouco documentado |
| App campo | `runtime/.../field_app.py` + `frontend/.../field/` | **8200** | Runbook OK |
| Modelo locker (cadastro) | `order_pickup_service/app/models/locker.py` | DB pickup | Sprint PPL; serviços separados não no compose |

**Fronteira já documentada:** COO ≠ runtime — ver `docs/runbooks/coo-portal-5180.md` (secção “Fronteira COO e runtime”).

---

## 3. Documentado mas não implementado (ou só stub)

### 3.1 Arquitetura e handoff (P0 documentação + comunicação)

| Gap | Onde está escrito | Realidade em `01_source/` |
|-----|-------------------|---------------------------|
| Backends regionais `backend_sp` / `backend_pt` | `docs/architecture/ellan_code_map.md`, `ellan_order_full_flow.md`, `ELLAN_DECISION_BOARD.md`, `ellan_fast_intervention_map.md`, `HANDOFF.md`, `ROADMAP.md` | **Removidos**; substituídos por `backend/runtime` |
| Portas 8201 / 8202 por região | Mesmos + compose comments históricos | **8200** único `backend_runtime` |
| Proxies Vite `/api/sp`, `/api/pt` | `HANDOFF.md`, `ROADMAP.md` | **Inexistentes** em `frontend/vite.config.ts` |
| `order_lifecycle_worker` como pasta top-level | Vários mapas | Worker no **mesmo** repo `backend/order_lifecycle_service` + serviço compose |

**Entrega de código:** não é feature nova — **atualizar** `docs/architecture/*`, `HANDOFF.md`, `ROADMAP.md`, `docs/visao_order_pickup_service.md` (secção “estado actual”) para apontar só para `backend/runtime`.

### 3.2 Portal COO (P1 produto)

| Capacidade API | Estado backend | Estado frontend |
|----------------|----------------|-----------------|
| Dashboard consolidado, widgets, KPIs, SLA, logística (leitura) | **Implementado** (`app/services/coo/*`) | **Dashboard** (`Dashboard.tsx`) |
| Sub-rotas (health, manifests, routing, inventory, SLA, penalties, compliance, KPIs, approvals) | **Implementado** (GET) | **Placeholder** (`CooSubpages.tsx` → `Placeholder.tsx`) |
| Penalidades aplicadas | **Stub vazio** (`portal_5180.py`) | Placeholder |
| POST aprovações SLA / expansão | **Stub fila** (`operations_service.py`) | `CooApprovalForm.tsx` existe mas rotas usam placeholder |
| `CooDataView` genérico | N/A | **Componente não ligado** ao router |

**Entrega:** substituir placeholders por `CooDataView` ou páginas dedicadas; persistir penalties + fila de aprovações.

### 3.3 NOC / rede de lockers (P0 operacional)

| Item | Doc | Código |
|------|-----|--------|
| SIMT / resumo lockers | `docs/runbooks/noc-simt-mvp.md` → runtime :8200 | `runtime/app/routers/noc.py` — **valores fixos** (ex.: `lockers.total: 1`) |
| Dashboard agregado | `mvp_progress_dashboard.md` T10 | `order_lifecycle_service/.../noc.py` — lê DB/eventos |
| UI NOC | Runbook + FE | `frontend/src/pages/noc/Dashboard.tsx` chama **8200 e 8010** |

**Entrega:** unificar contrato NOC (runtime alimenta telemetria real ou lifecycle é fonte de verdade); remover stub de produção.

### 3.4 Decomposição microserviços (P2 estratégico)

`docs/visao_order_pickup_service.md` e sprints descrevem extração para catalog, inventory, wallet, logistics.

| Serviço | Existe em `01_source/` | No `02_docker/docker-compose.yml` |
|---------|------------------------|-------------------------------------|
| `catalog_service` | Sim | **Não** |
| `inventory_service` | Sim | **Não** |
| `wallet_service` | Sim | **Não** |
| `logistics_service` | Sim | **Não** |
| `notification_service` | Sim | **Não** |
| `locker_operations` (scaffold) | Sim (mínimo) | **Não** |

**Entrega:** ou wire no compose + contratos HTTP, ou marcar explicitamente “lab-only / futuro” nos sprints para não constar como entregue.

### 3.5 E2E e paths de teste (P0 QA)

| Documentado | Real |
|-------------|------|
| Playwright checkout em `01_source/frontend/e2e/` | Specs em **`01_source/frontend_v0/e2e/`** |
| `07_tests/e2e_payment_ui_playwright.sh` corre em `frontend` | Pacote v1 **sem** specs Playwright |
| Regressão “12/12” = produto completo | `docs/regression_final_report.md` — sobretudo **build + scripts**; MVP dashboard: **9 tarefas Not Started** (T12–T21, T25) |

### 3.6 Deploy cloud (P2)

`deploy/README.md` — baseline ECS; **sem Helm chart**. Não bloqueia dev locker, bloqueia “entrega cloud” documentada.

---

## 4. Implementado mas pouco ou mal documentado

| Implementação | Path | Ação doc |
|---------------|------|----------|
| Runtime multi-locker único | `01_source/backend/runtime/README.md` | Propagar para `docs/architecture/*` |
| `partner_service` + proxy 8402 | `02_docker/docker-compose.yml`, `vite.config.ts` | Atualizar `HANDOFF.md` |
| API executive CEO | `order_pickup_service/app/routers/executive_dashboard.py` | Novo capítulo em doc API ou runbook CEO |
| Runtime sync pickup ↔ runtime | `order_pickup_service/app/workers/runtime_sync_worker.py` | Runbook ops / pickup |
| Login CEO/COO via `ecommerce_partners` | `partners.py` + runbook COO §5.1 | Já no runbook COO; falta runbook CEO |
| CI: `backend-test-collect`, payment contract, e2e-payment | `.github/workflows/` | Índice em `docs/HANDOFF.md` |
| dbt `locker_pnl` | `billing_fiscal_service/dbt_financial/models/marts/locker_pnl.sql` | Ligar a `docs/FA5_*` com path real |

---

## 5. Contradições críticas (corrigir antes de go-live locker)

| # | Tema | Valor A | Valor B | Fix recomendado (código/config) |
|---|------|---------|---------|----------------------------------|
| 1 | Porta pickup | Compose **8003** | Vite/COO smoke **8002** | Default `ORDER_PICKUP_SERVICE_PROXY=http://localhost:8003` em `vite.config.ts`; `07_tests/e2e_coo_smoke.sh`; exemplos em `docs/api/coo-portal-api.md` |
| 2 | Proxy `/api/runtime` | Deveria ser locker edge | `target: partnerServiceProxy` (8402) | `target: http://localhost:8200` (env `RUNTIME_SERVICE_PROXY`) |
| 3 | NOC fonte | Runbook → runtime | MVP T4 → lifecycle; FE usa ambos | Decisão: lifecycle agrega, runtime expõe health hardware; documentar e alinhar `noc.py` runtime |
| 4 | Login COO/CEO | `partner_service` devolve `partner` | Pickup infere perfil por `partner_id` | Doc + opcional: pickup login primário ou `partner_service` devolver `role` real |
| 5 | 5180 | Vite `dev:coo` | nginx compose `5180:80` | Glossário no runbook COO (já parcial) |
| 6 | Regressão vs MVP | 12/12 PASS | 64% tickets MVP | Alinhar `mvp_progress_dashboard.md` com scope real |

---

## 6. Backlog de entrega de código (priorizado)

### P0 — Bloqueia operação locker correta em dev/staging

1. **Proxy runtime no frontend** — `01_source/frontend/vite.config.ts`: `/api/runtime` → `http://localhost:8200` (não partner).
2. **Alinhar porta pickup** — defaults 8003 em Vite, smoke COO, README COO; comentário no compose (8402:8002 vs order_pickup 8003).
3. **NOC runtime** — `backend/runtime/app/routers/noc.py`: ler registry/DB real (ou delegar 100% ao lifecycle e deprecar rota stub).
4. **Testes runtime (mínimo)** — pytest para allocate/commit/open usados por `07_tests/e2e_payment_minimal_stack.sh` e `LockerBackendClient`.
5. **Testes lifecycle (mínimo)** — pytest para deadline/cancel após `payment-confirm` (libertação de slot).
6. **Atualizar docs arquitetura** — substituir `backend_sp/pt` por `backend/runtime` nos ficheiros listados na §3.1.

### P1 — MVP COO / ops / parceiro utilizável

7. **COO sub-páginas** — trocar `Placeholder.tsx` por `CooDataView` ou ecrãs (`frontend/src/router/index.tsx`, `CooSubpages.tsx`).
8. **COO penalties + approvals** — persistência ou integração real (`sla_service`, `operations_service`).
9. **CEO** — documentar credenciais + API; opcional menu v1 (`ExecutiveLayout`, rotas).
10. **Login unificado** — `partner_service` retornar `role`/`profile` ou frontend preferir sempre `/api/v1/partners/login` quando perfil ≠ partner.
11. **Fechar tickets MVP T12–T14, T18–T21** — definir scope ou cortar explicitamente (`docs/mvp_progress_dashboard.md`).

### P2 — Escala e visão de produto

12. **Compose “full lab”** — profile opcional com catalog, inventory, logistics, wallet.
13. **Migração v0→v1** — checkout público, kiosk (`docs/runbooks/frontend-v0-v1-migration.md` + código).
14. **E2E payment UI** — mover/duplicar specs para v1 ou corrigir CI para `frontend_v0`.
15. **Helm/K8s** — `deploy/` ou cortar da doc de entrega.
16. **Grafana dashboards** — conteúdo vs `docs/FA5_DASHBOARDS_GRAFANA_METABASE.md`.

---

## 7. Domínio LOCKERS — checklist de entrega

Fluxo físico esperado (alinhado a `docs/modelo_estados_definitivo.md` e runtime):

```text
allocate (runtime) → reserved/paid (pickup) → payment-confirm → commit (runtime)
→ opened_for_pickup → picked_up / expired / released
```

| Etapa | Dono código | Teste existente | Gap |
|-------|-------------|-----------------|-----|
| Allocate slot | `backend/runtime` | E2E payment stack | Sem pytest unitário |
| Estado alocação pickup | `order_pickup_service` models/allocation | Parcial em pickup tests | — |
| Confirm payment → commit | gateway + pickup + runtime | `make e2e-payment-p0` | — |
| Pickup / QR / kiosk | `order_pickup_service` | Kiosk tests parciais | — |
| Deadline / expire slot | `order_lifecycle` + worker | **Nenhum** pytest lifecycle | **P0** |
| Cadastro locker (região, slots) | `models/locker.py` + seeds | Seeds / smoke | Microserviços inventory não wired |
| COO “uptime / frota” | KPIs sobre lockers ativos | COO smoke mocked/live | Proxy/porta; UI placeholder |
| Campo (checklist locker) | `field_app.py` | `07_tests/smoke_app_campo_mvp.sh` | Depende proxy runtime (P0) |

---

## 8. Matriz docs → ficheiro de código (referência rápida)

| Documento | Alinhado? | Notas |
|-----------|-----------|-------|
| `docs/runbooks/coo-portal-5180.md` | **Sim** (com ressalvas porta 8002/8003) | Manter como runbook COO |
| `docs/api/coo-portal-api.md` | **Sim** | Atualizar exemplos host :8003 |
| `docs/runbooks/noc-simt-mvp.md` | **Parcial** | Stub runtime |
| `docs/runbooks/app-campo-mvp.md` | **Parcial** | Proxy runtime |
| `docs/runbooks/frontend-v0-v1-migration.md` | **Sim** | Migração incompleta |
| `docs/E2E_PAYMENT_MINIMAL_STACK_DESIGN.md` | **Parcial** | Path e2e errado para v1 |
| `docs/architecture/*` | **Não** | SP/PT obsoleto |
| `docs/HANDOFF.md`, `ROADMAP.md` | **Não** | Portas e backends antigos |
| `docs/visao_order_pickup_service.md` | **Aspiração** | Não reflete compose actual |
| `docs/Sprint_products_partners_lockers.md` | **Rever** | “Concluído” vs serviços fora compose |
| `docs/mvp_progress_dashboard.md` | **Interno** | 9 tickets em aberto |
| `docs/regression_final_report.md` | **QA** | Não substitui gaps acima |

---

## 9. Ordem sugerida de execução (sprint locker)

1. **Semana 1 (P0):** proxies/portas + pytest runtime/lifecycle mínimo + doc architecture refresh.  
2. **Semana 2 (P0/P1):** NOC contrato único + smoke verde com compose 8003/8200.  
3. **Semana 3 (P1):** COO UI sub-rotas + penalties/approvals.  
4. **Paralelo (P2):** v0/v1 checkout ou compose microserviços — decisão de produto.

---

## 10. Critérios de “feito” para esta iniciativa

- [ ] Nenhum doc em `docs/architecture/` referencia `backend_sp`/`backend_pt` como código activo.  
- [ ] `npm run dev` + compose: páginas NOC e campo falam com **8200** sem 502 silencioso.  
- [ ] COO smoke e dashboard funcionam com pickup em **8003** (compose).  
- [ ] `make e2e-payment-p0` verde + ≥1 teste pytest em runtime e lifecycle.  
- [ ] ≤3 rotas COO em placeholder (ou zero, se MVP exige portal completo).  
- [ ] `mvp_progress_dashboard.md` actualizado ou tickets T12–T21 fechados/cortados.

---

## 11. Referências no repositório

- Runtime: `01_source/backend/runtime/README.md`  
- Pickup / locker model: `01_source/order_pickup_service/app/models/locker.py`, `pickup.py`, `allocation.py`  
- Compose: `02_docker/docker-compose.yml`  
- Testes integração: `07_tests/`, `Makefile` (`test-collect`, `e2e-payment-p0`)  
- COO: `docs/api/coo-portal-api.md`, `docs/runbooks/coo-portal-5180.md`  
- Estados: `docs/modelo_estados_definitivo.md`

---

*Documento gerado por comparação estática `docs/` ↔ `01_source/` + `02_docker/`. Revalidar após merges grandes em frontend, pickup ou runtime.*
