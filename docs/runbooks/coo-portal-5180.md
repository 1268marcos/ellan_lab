# COO Portal 5180 — Runbook

Owner: FE + BE (order_pickup_service)  
Serviços: `01_source/frontend` (UI), `01_source/order_pickup_service` (API COO)

## Identificação

| Campo | Valor |
|-------|-------|
| Portal ID | 5180 (porta padrão do **frontend** `npm run dev:coo` / `dev:ceo`) |
| Role | COO (Chief Operations Officer) |
| UI (React) | `BrowserRouter` com `basename="/v1"` — rotas sob **`/v1/coo/*`** no browser |
| API base (HTTP) | **`/api/v1/coo`** no `order_pickup_service` (ex.: `http://localhost:8002/api/v1/coo`) |
| Router OpenAPI | Prefixo único `tags=["COO Portal 5180"]` + rotas base em `app/routers/coo/` |

**Nota:** “5180” refere-se ao **host/porta do Vite** do hub frontend, não ao path da API. O path canónico do portal na app é `/v1/coo/...` (URL completa `http://<host>:5180/v1/coo/dashboard` em dev).

## Documentação relacionada

| Documento | Path |
|-----------|------|
| **Referência API** (endpoints, exemplos request/response) | [`docs/api/coo-portal-api.md`](../api/coo-portal-api.md) |
| **README desenvolvimento** (UI COO) | [`01_source/frontend/src/pages/coo/README.md`](../../01_source/frontend/src/pages/coo/README.md) |
| **OpenAPI** (contrato vivo) | Com a app FastAPI em execução: `GET /docs` ou `GET /openapi.json` no host do `order_pickup_service` |

## Arquitetura resumida

1. **Frontend** (`01_source/frontend`): layout `COOLayout`, dashboard `COODashboard`, proxy Vite `'/api/v1/coo'` → `ORDER_PICKUP_SERVICE_PROXY` (default `http://localhost:8002`).
2. **Backend** (`order_pickup_service`): `app/routers/coo/` (`portal.py` + `portal_5180.py`), serviços em `app/services/coo/`, schemas em `app/schemas/coo/`.
3. **Auth COO** (`require_coo_access`): Bearer com utilizador **coo / ceo / ops**, ou **`X-API-Key`** de parceiro elegível (ex.: `code` COO/OPS ou `tier` OPERATIONS — ver `app/routers/coo/deps.py`).

## Pré-requisitos

- `order_pickup_service` a responder (local **8002** ou compose **8402→8002**, etc.).
- Para chamadas `curl` à API: **`COO_API_KEY`** ou token **`COO_BEARER_TOKEN`** (utilizador com role).
- Para smoke shell: **`jq`** instalado.

## 1. Smoke test (API)

Todas as rotas abaixo exigem cabeçalho de autenticação; sem isso devolve **403** `COO_ACCESS_REQUIRED`.

```bash
export ORDER_PICKUP_URL="${ORDER_PICKUP_URL:-http://localhost:8002}"
export COO_API_KEY="sua-chave-ou-token"   # ou COO_BEARER_TOKEN

curl -fsS -H "X-API-Key: ${COO_API_KEY}" \
  "${ORDER_PICKUP_URL}/api/v1/coo/widgets/summary" | jq .

curl -fsS -H "X-API-Key: ${COO_API_KEY}" \
  "${ORDER_PICKUP_URL}/api/v1/coo/dashboard/consolidated?days=7" | jq .

curl -fsS -H "X-API-Key: ${COO_API_KEY}" \
  "${ORDER_PICKUP_URL}/api/v1/coo/health/pickups" | jq .
```

**Suite shell (recomendado):** valida meta, widgets, dashboard, health, manifests, SLA, uptime, approvals.

```bash
export COO_API_KEY="…"
bash 07_tests/e2e_coo_smoke.sh
```

Variáveis úteis: `ORDER_PICKUP_URL`, `COO_API_KEY`, `COO_BEARER_TOKEN`.

## 2. Mapa de endpoints (API)

Base: `{ORDER_PICKUP_URL}/api/v1/coo`

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/meta` | Metadados do portal |
| GET | `/dashboard/consolidated` | Dashboard OPS consolidado (`days`) |
| GET | `/health/pickups` | Saúde de pickups (`region` opcional) |
| GET | `/deadlines/urgent` | Deadlines urgentes |
| GET | `/logistics/manifests/active` | Manifestos ativos |
| GET | `/logistics/routing/realtime` | Roteirização |
| GET | `/logistics/inventory/by-depot` | Inventário por depot |
| GET | `/suppliers/sla` | SLA por fornecedor (`period`) |
| GET | `/suppliers/penalties` | Penalidades |
| GET | `/suppliers/compliance` | Compliance |
| GET | `/kpis/network/uptime` | Uptime rede (`days`) |
| GET | `/kpis/mttr` | MTTR (`incident_type` opcional) |
| GET | `/kpis/fleet/efficiency` | Eficiência frota (`days`) |
| GET | `/approvals/pending` | Aprovações pendentes |
| POST | `/approvals/sla/adjust` | Stub fila SLA |
| POST | `/approvals/expansion` | Stub fila expansão |
| GET | `/widgets/summary` | Resumo widgets dashboard |

## 3. Smoke / E2E frontend (Playwright)

Testes de UI com mocks de API e Vite dedicado (porta default **5193** — ver `07_tests/playwright.config.ts`).

```bash
cd 07_tests
npm install
npx playwright install chromium
CI=1 npx playwright test e2e_coo_portal.spec.ts --config=playwright.config.ts
```

- `COO_E2E_PORT`: porta do dev server nos testes (default `5193`).
- `COO_E2E_SLOW=1`: inclui teste longo (~31 s) de estabilidade do KPI.
- `VITE_E2E_CACHE`: definido pelo Playwright para cache do Vite em diretório temporário (evita EACCES em `.vite-cache`).

## 4. Regressão COO (API + Playwright + build)

```bash
bash 07_tests/regression_coo.sh
```

Fluxo: smoke API (se `COO_API_KEY` ou `COO_BEARER_TOKEN` definido) → Playwright → `npm run build` no frontend → aviso de tamanho agregado de `dist/assets/*.js`.

## 5. Desenvolvimento local (UI)

```bash
cd 01_source/frontend
npm install
npm run dev:coo
```

Abrir **`http://127.0.0.1:5180/v1/login`**, autenticar com **partner_id** + **api_key** cujo perfil resolvido seja **coo** (ou ajustar env `VITE_PARTNER_ID`). Após login, o utilizador **coo** é redirecionado para **`/v1/coo/dashboard`**.

## 6. Troubleshooting

| Sintoma | Ação |
|---------|------|
| **403** em `/api/v1/coo/*` | Confirmar `X-API-Key` ou Bearer; parceiro deve ser elegível COO/OPS ou utilizador com role coo/ceo/ops. |
| UI sem dados / erros de rede | Verificar proxy `ORDER_PICKUP_SERVICE_PROXY` e se o pickup está a correr na URL alvo. |
| `e2e_coo_smoke.sh` falha `jq` | Instalar `jq`. |
| Playwright: porta em uso | `export COO_E2E_PORT=5194` (ou livrar a porta com `fuser -k <port>/tcp`). |
| Playwright: EACCES no cache Vite | Garantir `VITE_E2E_CACHE` (automático no `webServer` do Playwright) ou corrigir permissões de `01_source/frontend/.vite-cache`. |
| Login COO cai no dashboard errado | Confirmar resposta de login com `profile: "coo"` e redirect em `Login.tsx` para `/coo/dashboard`. |

## 7. Rollback / feature flag

- API: remover ou desativar `include_router(coo.router)` em `app/main.py` **não** é recomendado em produção sem janela; preferir bloqueio na gateway ou `require_coo_access` mantido.
- Frontend: rotas `/coo` ficam atrás de `CooPortalGate` (perfil `coo`); desligar exposição no router só com deploy coordenado.

## 8. Evidência esperada (smoke)

- `GET /widgets/summary` → JSON com `sla_violated_24h`, `deliveries_today`, `lockers_offline`, etc.
- `GET /dashboard/consolidated?days=7` → JSON com `horizon_days`, `orders_in_window`, campos de pickups opcionais, etc.
- Script `e2e_coo_smoke.sh` termina com `All COO portal smoke tests passed!`.

## 9. Referências no repositório

| Artefacto | Path |
|-----------|------|
| Smoke API | `07_tests/e2e_coo_smoke.sh` |
| E2E Playwright | `07_tests/e2e_coo_portal.spec.ts`, `07_tests/playwright.config.ts` |
| Regressão | `07_tests/regression_coo.sh` |
| Rotas COO | `01_source/order_pickup_service/app/routers/coo/portal_5180.py` |
| Auth | `01_source/order_pickup_service/app/routers/coo/deps.py` |
| UI dashboard | `01_source/frontend/src/pages/coo/Dashboard.tsx` |
| Proxy Vite | `01_source/frontend/vite.config.ts` |
| Referência API (Markdown) | `docs/api/coo-portal-api.md` |
| README dev portal COO | `01_source/frontend/src/pages/coo/README.md` |

## Contato / owner

- Ajustar owner e canal de escalação operacional conforme a equipa ELLAN LAB.
