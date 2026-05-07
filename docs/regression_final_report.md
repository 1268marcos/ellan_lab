# Regression Final Report - Thu May  7 16:56:40 -03 2026

### Frontend Build
```bash
$ cd 01_source/frontend && npm run build

> ellan-frontend@0.0.1 build
> tsc -b && vite build

vite v5.4.21 building for production...
transforming...
✓ 954 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                            0.53 kB │ gzip:   0.34 kB
dist/assets/index-BirY6B9j.css            45.09 kB │ gzip:   7.82 kB
dist/assets/lifecycle-afJM9zhS.js          0.40 kB │ gzip:   0.25 kB
dist/assets/runtime-CqPdPpRK.js            1.14 kB │ gzip:   0.57 kB
dist/assets/billing-DdrlJ9M_.js            1.22 kB │ gzip:   0.55 kB
dist/assets/Allocations-CvfUybAh.js        3.17 kB │ gzip:   1.10 kB
dist/assets/Dashboard-DNFZepCJ.js          3.54 kB │ gzip:   1.21 kB
dist/assets/CreditNotes-DxiObohk.js        4.71 kB │ gzip:   1.79 kB
dist/assets/OpsLockerStatus-CWACzlpO.js    4.88 kB │ gzip:   1.64 kB
dist/assets/OpsPickupFlow-DttaXD6s.js      5.52 kB │ gzip:   1.76 kB
dist/assets/Disputes-TXLlkaGG.js           5.72 kB │ gzip:   2.04 kB
dist/assets/PartnerInvoices-BSuwmqo9.js    5.92 kB │ gzip:   2.26 kB
dist/assets/Health-DHsB_T7f.js             6.00 kB │ gzip:   2.14 kB
dist/assets/BillingCycles-BciPS1xw.js      6.44 kB │ gzip:   2.06 kB
dist/assets/Metrics-C8DaFceJ.js            6.80 kB │ gzip:   2.37 kB
dist/assets/Ranking-DMs5-PUG.js            7.91 kB │ gzip:   2.35 kB
dist/assets/index-oeDgxqzP.js            788.04 kB │ gzip: 227.62 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 7.50s
PASS
```

### Frontend_v0 Build
```bash
$ cd 01_source/frontend_v0 && npm run build

> frontend@0.0.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 2602 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                                   2.44 kB │ gzip:   0.98 kB
dist/assets/OpsKioskTouchModelsPage-C2Eobhb6.css                  9.24 kB │ gzip:   1.93 kB
dist/assets/PublicCheckoutPage-CTw-A3fF.css                      12.76 kB │ gzip:   2.43 kB
dist/assets/RouteOptimizePage-CIGW-MKW.css                       15.61 kB │ gzip:   6.46 kB
dist/assets/index-BL91oUr3.css                                   19.83 kB │ gzip:   4.82 kB
dist/assets/fiscalSprint3PartnerAuditMirror-DHHRZ1ai.js           0.35 kB │ gzip:   0.24 kB
dist/assets/orderLifecycleInternalApi-B_z3a5MA.js                 0.38 kB │ gzip:   0.29 kB
dist/assets/opsDateTimeFormat-CQNp5cgB.js                         0.53 kB │ gzip:   0.27 kB
dist/assets/OpsActionButton-D8Cv3rG0.js                           0.60 kB │ gzip:   0.38 kB
dist/assets/RuntimeOpsSubnav-ytUw2qG-.js                          0.66 kB │ gzip:   0.41 kB
dist/assets/myAreaSharedFormStyles-BRiG8CQ4.js                    0.68 kB │ gzip:   0.40 kB
dist/assets/useOpsWindowPreset-BQKD76y5.js                        0.69 kB │ gzip:   0.42 kB
dist/assets/fiscalScopeSummary-91jD4X1r.js                        0.71 kB │ gzip:   0.44 kB
dist/assets/OpsScenarioPresets-DMiwCEeo.js                        0.75 kB │ gzip:   0.46 kB
dist/assets/PublicAccessDeniedPage-qIXo4n4G.js                    0.78 kB │ gzip:   0.47 kB
dist/assets/fiscalD11OrderIdRollup-DZwQs3ve.js                    0.82 kB │ gzip:   0.47 kB
dist/assets/fiscalSprint2FinanceGate-CP6Ikr3V.js                  0.85 kB │ gzip:   0.48 kB
dist/assets/runtimeOpsApi-ItCRxj39.js                             0.87 kB │ gzip:   0.56 kB
dist/assets/OpsDiscontinuedEllanLabPage-dEroJLwF.js               1.17 kB │ gzip:   0.63 kB
dist/assets/PublicEmailVerificationPage-DVfpm7TN.js               1.29 kB │ gzip:   0.73 kB
dist/assets/OpsRuntimeHealthPage-BOf5FXAW.js                      1.34 kB │ gzip:   0.74 kB
dist/assets/PublicFiscalDataPage-Brn9KWWQ.js                      1.52 kB │ gzip:   0.89 kB
dist/assets/opsVisualTokens-CBGU8sGA.js                           1.54 kB │ gzip:   0.66 kB
dist/assets/paymentProfile-6kI5D2gh.js                            1.54 kB │ gzip:   0.81 kB
dist/assets/runtimeOpsPageChrome-BRjx8Ipt.js                      1.70 kB │ gzip:   0.74 kB
dist/assets/OpsTrendKpiCard-CLakxfUn.js                           1.71 kB │ gzip:   0.91 kB
dist/assets/billingFiscalOpsApi-DLoQrnzD.js                       1.71 kB │ gzip:   0.86 kB
dist/assets/BillingInvoiceSearchPage-CrHU7GZ0.js                  1.96 kB │ gzip:   1.00 kB
dist/assets/OpsRuntimeSlotsMonitorPage-D_haQvnF.js                2.10 kB │ gzip:   1.01 kB
dist/assets/BillingInvoiceQueuePage-CSd8O1un.js                   2.10 kB │ gzip:   0.97 kB
dist/assets/OpsRuntimeEventLogPage-Bf6eDHok.js                    2.52 kB │ gzip:   1.20 kB
dist/assets/publicApi-BJUlIfg7.js                                 2.58 kB │ gzip:   1.01 kB
dist/assets/BillingKpiDailyPage-FF6NR-o0.js                       2.60 kB │ gzip:   1.13 kB
dist/assets/BillingReconciliationGapsPage-DuYWn5qJ.js             2.64 kB │ gzip:   1.16 kB
dist/assets/OrderDeadlinesPage-CQtJT5PR.js                        2.72 kB │ gzip:   1.18 kB
dist/assets/fiscalSprint2D18Content-BictLWvT.js                   2.84 kB │ gzip:   1.38 kB
dist/assets/fiscalD10ProvidersTracker-_0_cM13O.js                 2.89 kB │ gzip:   1.20 kB
dist/assets/fiscalApiCatalog-EnqWLzij.js                          2.99 kB │ gzip:   0.83 kB
dist/assets/OpsRentalPlansPage-VRyGkQYq.js                        3.17 kB │ gzip:   1.49 kB
dist/assets/PublicRegionHubPage-BUacIVTt.js                       3.33 kB │ gzip:   1.33 kB
dist/assets/OpsVersioningPolicyPage-DDWC6JPx.js                   3.34 kB │ gzip:   1.36 kB
dist/assets/OpsAuthorizationPolicyPage-pMUkLq-F.js                3.37 kB │ gzip:   1.46 kB
dist/assets/PublicForgotPasswordPage-Dd-txneQ.js                  3.37 kB │ gzip:   1.47 kB
dist/assets/fiscalP01bDailyPackage-CwYZ8PmL.js                    3.59 kB │ gzip:   1.52 kB
dist/assets/OpsLockerOccupancyForecastPage-C58kcD72.js            4.41 kB │ gzip:   1.88 kB
dist/assets/OpsNotificationLogsPage-cdU1b0Ay.js                   4.55 kB │ gzip:   1.79 kB
dist/assets/OpsLogisticsManifestsOverviewPage-BMNr04b8.js         4.80 kB │ gzip:   2.04 kB
dist/assets/OpsIntegrationOrdersPartnerLookupPage-D9g5CxJ8.js     4.80 kB │ gzip:   2.10 kB
dist/assets/OrderDomainEventsPage-DwHokuaG.js                     4.97 kB │ gzip:   1.97 kB
dist/assets/PublicLandingPage-Bb1G9-qh.js                         4.97 kB │ gzip:   1.44 kB
dist/assets/myAreaSharedCardStyles-B_ISSF44.js                    5.11 kB │ gzip:   2.04 kB
dist/assets/OpsRentalContractsPage-D-Z4caok.js                    5.58 kB │ gzip:   2.10 kB
dist/assets/OpsIntelligencePage-CL46mNt2.js                       5.60 kB │ gzip:   2.08 kB
dist/assets/PublicSecurityPage-v4gqDNvJ.js                        5.61 kB │ gzip:   2.32 kB
dist/assets/PublicNotFoundPage-BBIEwI6k.js                        5.74 kB │ gzip:   1.82 kB
dist/assets/PublicFiscalSearchPage-CFZlHpX1.js                    5.84 kB │ gzip:   2.17 kB
dist/assets/fiscalSprint3IncidentRunbook-CunGrQ08.js              6.22 kB │ gzip:   2.82 kB
dist/assets/OpsPricingRulesPage-BdSsc14C.js                       6.67 kB │ gzip:   2.40 kB
dist/assets/OpsLockerProductConfigPage-DpAHkQ7Y.js                6.75 kB │ gzip:   2.55 kB
dist/assets/OpsLogisticsInventoryPage-CogLjcxH.js                 6.81 kB │ gzip:   2.06 kB
dist/assets/FiscalDepartmentDashboardsPage-3qHCCR6n.js            6.92 kB │ gzip:   2.65 kB
dist/assets/OpsProductBundlesPage-VZH12wW6.js                     7.36 kB │ gzip:   2.70 kB
dist/assets/PublicLoginPage-C2LFXtiY.js                           7.38 kB │ gzip:   2.78 kB
dist/assets/PublicMyCreditsPage-DeZZE9Ay.js                       7.48 kB │ gzip:   3.16 kB
dist/assets/OpsReturnTrackingPage-Zg5-Tl4T.js                     7.49 kB │ gzip:   2.84 kB
dist/assets/OpsLockerSlotsPage-5YTBrDW1.js                        8.05 kB │ gzip:   3.02 kB
dist/assets/FiscalSprint2FinanceGatePage-B_2t5PrE.js              8.26 kB │ gzip:   3.13 kB
dist/assets/OpsIntegrationOrdersFiscalPage-CqMwE5iD.js            8.38 kB │ gzip:   3.19 kB
dist/assets/FiscalProfileForm-DkS4-5gW.js                         8.72 kB │ gzip:   2.39 kB
dist/assets/browser-DluvSNNp.js                                   8.88 kB │ gzip:   4.46 kB
dist/assets/OpsPartnersHypertablesPage-eLpnDtuo.js                9.37 kB │ gzip:   3.50 kB
dist/assets/OpsPartnersDashboardPage-BWoe1wkj.js                  9.57 kB │ gzip:   3.34 kB
dist/assets/PaymentReconciliationPage-CnLY75uj.js                 9.57 kB │ gzip:   3.14 kB
dist/assets/OpsProductCategoriesPage-BRYxgkZk.js                  9.93 kB │ gzip:   3.44 kB
dist/assets/DevLockerResetPage-aq9SLk_N.js                       10.11 kB │ gzip:   3.15 kB
dist/assets/FiscalSprint3PartnerAuditPage-DLB2oUOy.js            10.28 kB │ gzip:   3.90 kB
dist/assets/FiscalPartnerPerformancePage-BAjpqihl.js             10.34 kB │ gzip:   3.55 kB
dist/assets/PublicRegisterPage-D1bKiKXx.js                       10.74 kB │ gzip:   3.60 kB
dist/assets/OpsQuickEnablementPage-CqHQbrAc.js                   10.92 kB │ gzip:   4.32 kB
dist/assets/OpsLogisticsDashboardPage-DnY1lAI3.js                11.20 kB │ gzip:   3.74 kB
dist/assets/OpsPartnersFinancialsServiceAreasPage-r-6ByZEn.js    11.22 kB │ gzip:   3.91 kB
dist/assets/PartnerSettlementPage-DJVUpym8.js                    11.23 kB │ gzip:   3.70 kB
dist/assets/OpsLockerOperatorsPage-Cv1USJTE.js                   11.36 kB │ gzip:   3.62 kB
dist/assets/OpsRuntimeSyncPage-ZGBdclyD.js                       11.60 kB │ gzip:   4.13 kB
dist/assets/DevSlotAllocationPage-C7DgdoGK.js                    12.03 kB │ gzip:   3.99 kB
dist/assets/OpsReconciliationPage-j6t69oY7.js                    12.25 kB │ gzip:   4.17 kB
dist/assets/OpsProductsInventoryHealthPage-RT7GpRef.js           12.29 kB │ gzip:   3.99 kB
dist/assets/PublicTermsOfUsePage-DCi5lMTa.js                     12.34 kB │ gzip:   3.64 kB
dist/assets/OpsProductsAssetsPage-BDukIlOG.js                    12.62 kB │ gzip:   3.27 kB
dist/assets/PublicPrivacyPolicyPage-B7dEMo7i.js                  12.77 kB │ gzip:   3.64 kB
dist/assets/OpsKioskTouchModelsPage-BHrnNCn3.js                  12.92 kB │ gzip:   4.43 kB
dist/assets/OpsProductsPricingFiscalPage-C3jjtE_3.js             13.26 kB │ gzip:   4.15 kB
dist/assets/OrderPickupExecutiveSummaryPage-BS94Ma3U.js          13.29 kB │ gzip:   4.24 kB
dist/assets/FiscalIncidentResponsePage-B6IO6gKo.js               15.10 kB │ gzip:   4.91 kB
dist/assets/OpsProductsCatalogPage-CUaymL_A.js                   15.64 kB │ gzip:   5.29 kB
dist/assets/ManualPickupPanel-U1KcEnnH.js                        15.72 kB │ gzip:   5.37 kB
dist/assets/OpsPromotionsPage-B5Irljyg.js                        16.54 kB │ gzip:   5.02 kB
dist/assets/PublicMyOrdersPage-CpAGzz5B.js                       16.56 kB │ gzip:   5.60 kB
dist/assets/index-B2bCM2zs.js                                    16.68 kB │ gzip:   6.28 kB
dist/assets/OpsIntegrationOutboxReplayPage-BAvafLC9.js           16.95 kB │ gzip:   5.34 kB
dist/assets/FiscalGlobalPage-y3XQnW1g.js                         17.05 kB │ gzip:   5.06 kB
dist/assets/FiscalReadinessExecutionPage-D-lGd2Q8.js             17.76 kB │ gzip:   5.62 kB
dist/assets/FiscalAccountingClosePage-BuU9JcSS.js                18.01 kB │ gzip:   5.83 kB
dist/assets/FiscalFg1GatePage-BYACDSzu.js                        18.26 kB │ gzip:   5.07 kB
dist/assets/FiscalCountriesPage-DPMCXJJd.js                      18.48 kB │ gzip:   5.30 kB
dist/assets/OpsPartnersBillingMonitoringPage-km0OZVZe.js         18.56 kB │ gzip:   5.00 kB
dist/assets/OpsLogisticsReturnsPage-DGcA-Bao.js                  19.46 kB │ gzip:   6.32 kB
dist/assets/PublicSupportPage-CSyrxPR2.js                        19.96 kB │ gzip:   6.32 kB
dist/assets/OpsLogisticsManifestsPage-CuVBV8FS.js                20.01 kB │ gzip:   5.78 kB
dist/assets/PublicCheckoutPage-CfmIPfV2.js                       21.58 kB │ gzip:   5.94 kB
dist/assets/OpsDevErrorsPage-Don-9TIF.js                         23.57 kB │ gzip:   7.46 kB
dist/assets/PublicCatalogPage-C30yQ4jy.js                        23.97 kB │ gzip:   7.21 kB
dist/assets/fiscalSprint4RegressionMatrix-Dq48Gwb1.js            25.67 kB │ gzip:   8.57 kB
dist/assets/DevBaseCatalogPage-PZwmmrMO.js                       25.74 kB │ gzip:   6.09 kB
dist/assets/OpsPartnersReconciliationDashboardPage-Ir8QfrbB.js   28.19 kB │ gzip:   8.29 kB
dist/assets/OpsPageTitleHeader-BM3MdcIB.js                       28.63 kB │ gzip:   8.44 kB
dist/assets/PublicOrderDetailPage-kabF13uq.js                    28.71 kB │ gzip:   8.28 kB
dist/assets/OrderPickupHealthPage-BlLjvAFT.js                    28.96 kB │ gzip:   8.32 kB
dist/assets/FiscalSprint4RegressionMatrixPage-CUpS4aE3.js        31.67 kB │ gzip:   7.50 kB
dist/assets/OpsFiscalProvidersPage-BltBScmg.js                   33.59 kB │ gzip:   8.90 kB
dist/assets/FiscalSloAlertsPage-LHuZfOqe.js                      36.39 kB │ gzip:  11.16 kB
dist/assets/FiscalManagementDailyPage-CApcdPXm.js                47.16 kB │ gzip:  12.17 kB
dist/assets/OpsAuditPage-DagkcqDq.js                             51.70 kB │ gzip:  14.09 kB
dist/assets/views-BL3w9UJQ.js                                    54.90 kB │ gzip:  13.80 kB
dist/assets/FiscalUpdatesPage-8P76A0P-.js                        62.50 kB │ gzip:  14.50 kB
dist/assets/RegionPage-DElaIKws.js                               72.07 kB │ gzip:  18.71 kB
dist/assets/LockerDashboard-B8WUjIKC.js                          91.19 kB │ gzip:  23.95 kB
dist/assets/OpsUpdatesHistoryPage-Bbqw8sqC.js                    96.68 kB │ gzip:  22.23 kB
dist/assets/OpsHealthPage-DwcrMfqm.js                           106.12 kB │ gzip:  26.44 kB
dist/assets/RouteOptimizePage-ClgORt67.js                       160.13 kB │ gzip:  46.82 kB
dist/assets/index-BORNL0LP.js                                   310.76 kB │ gzip:  93.93 kB
dist/assets/LineChart-7nf8pZ2S.js                               383.78 kB │ gzip: 105.69 kB
✓ built in 12.81s
PASS
```

### App Campo Smoke
```bash
$ ./smoke-app-campo.sh
{"ok":true,"service":"backend_runtime"}{"status":"ok","service":"field-app"}App Campo smoke OK
PASS
```

### NOC Smoke
```bash
$ ./smoke-noc.sh
{"status":"ok","database":"ok"}{"status":"ok"}{"status":"ok","service":"noc-simt","runtime":{"status":"ok"},"lifecycle":{"status":"unknown","mode":"mvp-polling"},"generated_at":"2026-05-07T19:57:08.591494Z"}NOC smoke OK
PASS
```

### Suporte Smoke
```bash
$ ./smoke-suporte.sh
{"status":"healthy","service":"order_pickup_service","timestamp":"2026-05-07T19:57:08.606414+00:00"}{"status":"ok","service":"support-n1-n2"}Suporte smoke OK
PASS
```

### Fiscal Smoke
```bash
$ ./smoke-fiscal.sh
== FISCAL ROUTES SMOKE ==
FRONTEND_BASE_URL=http://localhost:5173

[OK] FISCAL global -> 200 (marker não detectado via curl em SPA)
[OK] FISCAL updates -> 200 (marker não detectado via curl em SPA)
[OK] FISCAL countries -> 200 (marker não detectado via curl em SPA)
[OK] FISCAL sprint2 finance gate -> 200 (marker não detectado via curl em SPA)
[OK] FISCAL sprint3 partner audit -> 200 (marker não detectado via curl em SPA)

RESULTADO FINAL: FISCAL_ROUTES_SMOKE_OK
Fiscal smoke OK
PASS
```

### Proxy v0/v1
```bash
$ curl -fsSI http://localhost:5180/ | sed -n '1p'
HTTP/1.1 302 Found
PASS
```

### E2E App Campo
```bash
$ bash 07_tests/e2e_app_campo_mvp.sh
=== E2E App Campo MVP ===
RUNTIME_BASE_URL=http://localhost:8200
LOCKER_ID=SP-ALPHAVILLE-SHOP-LK-001
{"status":"accepted","item":{"locker_id":"SP-ALPHAVILLE-SHOP-LK-001","task":"install","status":"pending","timestamp":null}}
{"locker_id":"SP-ALPHAVILLE-SHOP-LK-001","status":"operational","slots_free":5}
E2E App Campo PASS
PASS
```

### E2E NOC
```bash
$ bash 07_tests/e2e_noc_simt_mvp.sh
=== E2E placeholder: NOC/SIMT MVP ===
Fluxo alvo: dashboard -> incidente -> acknowledge -> lifecycle dashboard.
=== Smoke: NOC/SIMT MVP ===
RUNTIME_BASE_URL=http://localhost:8200
LIFECYCLE_BASE_URL=http://localhost:8010
NOC_SIMT_SMOKE_OK
E2E_NOC_SIMT_MVP_PLACEHOLDER_OK
PASS
```

### E2E Suporte
```bash
$ bash 07_tests/e2e_suporte_n1_n2_mvp.sh
=== E2E placeholder: Suporte N1/N2 MVP ===
Fluxo alvo: consultar pedido -> timeline -> next_action -> escalonamento.
=== Smoke: Suporte N1/N2 MVP ===
ORDER_PICKUP_BASE_URL=http://localhost:8003
SUPORTE_N1_N2_SMOKE_OK
E2E_SUPORTE_N1_N2_MVP_PLACEHOLDER_OK
PASS
```

### E2E Offline Sync
```bash
$ bash 07_tests/e2e_offline_sync.sh
=== E2E: Offline Sync App Campo ===
E2E_OFFLINE_SYNC_OK
PASS
```

### Fiscal Go/No-Go
```bash
$ bash 02_docker/run_f3_go_no_go.sh
FISCAL GO/NO-GO: GO
Evidence: docs/fiscal_go_no_go_evidence.md
PASS
```

## Resumo
- **Passed:** 12
- **Failed:** 0
- **Total:** 12
**FINAL RESULT: ALL TESTS PASSED**
