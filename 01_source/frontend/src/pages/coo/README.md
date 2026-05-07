# Portal COO (frontend)

Área **`/v1/coo/*`** do hub React: dashboard operacional, navegação por secções e placeholders para rotas ainda sem UI dedicada.

## Pré-requisitos

- Node 20+ (recomendado)
- **`order_pickup_service`** acessível para o proxy Vite (por defeito `http://localhost:8002`)

## Arranque rápido

Na pasta do frontend:

```bash
cd 01_source/frontend
npm install
npm run dev:coo
```

Abrir **`http://127.0.0.1:5180/v1/login`**, autenticar com **partner_id** + **api_key** cujo perfil seja **`coo`**. O redirect pós-login leva a **`/v1/coo/dashboard`**.

> A app usa **`BrowserRouter basename="/v1"`** — todas as rotas internas são relativas a `/v1`.

## Variáveis de ambiente (Vite)

| Variável | Uso |
|----------|-----|
| `ORDER_PICKUP_SERVICE_PROXY` | URL do `order_pickup_service` para o proxy `'/api/v1/coo'` (ver `vite.config.ts`) |
| `VITE_PARTNER_ID` | Valor inicial do campo `partner_id` no login (opcional) |

## Estrutura de pastas

| Ficheiro / pasta | Função |
|------------------|--------|
| `COOLayout.tsx` | Sidebar, menu por secções, `<Outlet />` |
| `Dashboard.tsx` | `COODashboard` — widgets, gráficos Recharts, aprovações |
| `cooDashboardModel.ts` | Mapeamento das respostas da API para estado dos gráficos |
| `Placeholder.tsx` | Página genérica para sub-rotas sem ecrã dedicado |
| `CooSubpages.tsx` | Re-exporta placeholders com nomes das rotas |
| `../../styles/coo/` | Tema (`theme.ts`), `coo.css`, `global.css` |
| `../../api/coo.ts` | Cliente axios (`/api` + `/v1/coo/...`) |
| `../../components/coo/` | `WidgetsBar`, `GaugeChart`, `StatusIndicator`, ícones |

## Cliente API

- Base axios: **`/api`** (`src/api/client.ts`), com `X-API-Key` e `Authorization` a partir do auth guardado.
- Chamadas COO: **`src/api/coo.ts`** (`getJson`, `getWidgetsSummary`, posts de approvals).

## Testes E2E (Playwright)

Os testes vivem em **`07_tests/`** (não nesta pasta).

```bash
cd 07_tests
npm install
npx playwright install chromium
CI=1 npx playwright test e2e_coo_portal.spec.ts --config=playwright.config.ts
```

- Porta do servidor de teste: **`COO_E2E_PORT`** (default `5193`).
- **`VITE_E2E_CACHE`**: usado pelo Playwright para cache do Vite em `/tmp` (ver `playwright.config.ts`).

## Regressão + smoke API

Na raiz do monorepo:

```bash
export COO_API_KEY="…"   # opcional mas recomendado para o smoke
bash 07_tests/regression_coo.sh
```

## Documentação relacionada

- Runbook: `docs/runbooks/coo-portal-5180.md`
- Contrato HTTP: `docs/api/coo-portal-api.md`
