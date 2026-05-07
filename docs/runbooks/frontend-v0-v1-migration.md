# Frontend v0 -> v1 Migration Runbook

Owner: FE  
Contato emergencia: FE + QA no canal do sprint MVP  
Status: Sprint 1, T1/T2 executados

## T1 - Inventario de Rotas

Referencia de planejamento:
- `docs/p61-80.txt`: mapa de portais, migracao de `/v0`, criacao dos portais 5175/5176/5177/5178.
- `docs/p81-86.txt`: criterio de migracao `/v0` redireciona para portal correto baseado no perfil.

### Comandos equivalentes executados

Por restricao operacional do agente, a contagem/listagem foi feita com busca de arquivos do workspace em vez de `find/head`. Resultado equivalente ao comando pedido:

```bash
echo "=== ROTAS frontend_v0 ==="
find 01_source/frontend_v0/src/pages -name "*.jsx" -o -name "*.tsx" | wc -l
find 01_source/frontend_v0/src/pages -name "*.jsx" -o -name "*.tsx" | head -20

echo "=== ROTAS frontend ==="
find 01_source/frontend/src/pages -name "*.tsx" | wc -l
find 01_source/frontend/src/pages -name "*.tsx" | head -20
```

### Resultado

`frontend_v0`:
- Total de paginas `.jsx/.tsx`: 100
- Primeiras 20 encontradas:
  - `01_source/frontend_v0/src/pages/intelligence/views.jsx`
  - `01_source/frontend_v0/src/pages/legacy/RegionPageFirst.jsx`
  - `01_source/frontend_v0/src/pages/legacy/LockerDashboardFirst.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicFiscalSearchPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicLandingPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicMyCreditsPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicSecurityPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicEmailVerificationPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicForgotPasswordPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicCatalogPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicAccessDeniedPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicLoginPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicOrderDetailPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicTermsOfUsePage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicRegisterPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicSupportPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicRegionHubPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicMyOrdersPage.jsx`
  - `01_source/frontend_v0/src/pages/public/PublicFiscalDataPage.jsx`
  - `01_source/frontend_v0/src/pages/public/myAreaSharedComponents.jsx`

`frontend`:
- Total de paginas `.tsx`: 33
- Primeiras 20 encontradas:
  - `01_source/frontend/src/pages/partners/OpsPickupFlow.tsx`
  - `01_source/frontend/src/pages/partners/OpsLockerStatus.tsx`
  - `01_source/frontend/src/pages/runtime/Allocations.tsx`
  - `01_source/frontend/src/pages/runtime/Dashboard.tsx`
  - `01_source/frontend/src/pages/Landing.tsx`
  - `01_source/frontend/src/pages/support/SupportCenter.tsx`
  - `01_source/frontend/src/pages/legal/TermsOfUse.tsx`
  - `01_source/frontend/src/pages/legal/PrivacyPolicy.tsx`
  - `01_source/frontend/src/pages/lifecycle/Ranking.tsx`
  - `01_source/frontend/src/pages/lifecycle/Health.tsx`
  - `01_source/frontend/src/pages/lifecycle/Metrics.tsx`
  - `01_source/frontend/src/pages/intelligence/OccupancyForecast.tsx`
  - `01_source/frontend/src/pages/intelligence/PredictiveHealth.tsx`
  - `01_source/frontend/src/pages/intelligence/FeedbackInsights.tsx`
  - `01_source/frontend/src/pages/finance/Disputes.tsx`
  - `01_source/frontend/src/pages/finance/CreditNotes.tsx`
  - `01_source/frontend/src/pages/finance/PartnerInvoices.tsx`
  - `01_source/frontend/src/pages/finance/BillingCycles.tsx`
  - `01_source/frontend/src/pages/Login.tsx`
  - `01_source/frontend/src/pages/settings/Profile.tsx`

### Leitura tecnica

- `frontend_v0` concentra a maior parte das telas operacionais, fiscais, publicas e de kiosk.
- `frontend` ja usa `BrowserRouter basename="/v1"` e tem rotas canônicas modernas em TypeScript.
- `02_docker/nginx/frontends-v0-v1-proxy.conf` ja roteia:
  - `/v1/` -> `host.docker.internal:5173`
  - `/v0/` -> `host.docker.internal:5174`
  - `/` -> redirect para `/v1/`

## T2 - Decisao de Roteamento MVP

### Decisao

Manter `frontend` como portal canônico em `/v1` e manter `frontend_v0` como legado controlado em `/v0` durante as 4 sprints MVP.

### Regra de migracao por prioridade

1. Migrar ou criar em `/v1` primeiro:
   - Suporte N1/N2: rota base ja existe em `01_source/frontend/src/pages/support/SupportCenter.tsx`.
   - NOC/SIMT MVP: usar base `runtime/*`, `analytics/*`, `lifecycle/*` existentes em `/v1`.
   - App Campo MVP: criar nova area em `/v1/field/*` ou `/v1/ops/field/*`.
   - Fiscal MVP: manter paginas fiscais criticas no legado ate equivalentes canônicos existirem.

2. Manter em `/v0` temporariamente:
   - Telas fiscais avançadas.
   - Kiosk/public checkout legado.
   - OPS profundo ainda sem equivalente em `/v1`.

3. Nao remover `frontend_v0` no MVP:
   - A descontinuação completa fica para Sprint 5+.
   - O MVP exige fallback documentado, nao migração total.

### Como testar

```bash
bash 07_tests/smoke_frontend_v0_v1_migration.sh
```

Ou validar build local:

```bash
cd 01_source/frontend && npm run build
```

Opcional com os dois servidores ativos:

```bash
curl -I http://localhost/v1/
curl -I http://localhost/v0/
```

### Como reverter

1. Manter `02_docker/nginx/frontends-v0-v1-proxy.conf` com `/v0/` ativo.
2. Se uma rota migrada falhar em `/v1`, remover o link/menu novo e apontar temporariamente para a rota equivalente em `/v0/`.
3. Rebuildar somente o frontend afetado.

### Proximo passo

Sprint 1 FE W2:
- Criar mapa `rota v0 -> rota v1/canonical/fallback`.
- Selecionar ate 5 rotas P.ALTA para migracao MVP.

## Checklist de Aceite MVP

Smoke command:

```bash
bash 07_tests/smoke_frontend_v0_v1_migration.sh
```

E2E command:

```bash
bash 07_tests/e2e_frontend_v0_v1_migration_mvp.sh
```

Rollback:

1. Restaurar `02_docker/nginx/frontends-v0-v1-proxy.conf` para enviar todo fallback para `frontend-v0:5174`.
2. Remover links de menu em `/v1` para rotas migradas com falha.
3. Rebuildar `frontend` e manter `frontend_v0` ativo como canônico temporário.

Owners:

- Primario: @fe
- Apoio backend/proxy: @be
- Validacao: @qa
