# MVP Progress Dashboard - Thu May 7 2026

## Overall Status
| Metric | Value |
|--------|-------|
| Total Tasks | 25 |
| Completed | 16 |
| In Progress | 0 |
| Not Started | 9 |
| Completion % | 64% |
| Days Remaining | 30 |

## By Sprint
| Sprint | Tasks | Completed | Progress |
|--------|-------|-----------|----------|
| Sprint 1 | 7 | 7 | 100% |
| Sprint 2 | 6 | 4 | 67% |
| Sprint 3 | 6 | 3 | 50% |
| Sprint 4 | 6 | 2 | 33% |

## By Role
| Role | Tasks | Completed | Progress |
|------|-------|-----------|----------|
| FE | 6 | 4 | 67% |
| BE | 10 | 7 | 70% |
| FISC | 4 | 2 | 50% |
| QA | 5 | 3 | 60% |

## Ticket Status
| Ticket | Sprint | Role | Status | Evidence |
|--------|--------|------|--------|----------|
| T1 | Sprint 1 | FE | Completed | Route inventory documented in `docs/runbooks/frontend-v0-v1-migration.md` |
| T2 | Sprint 1 | FE | Completed | v0/v1 proxy config in `02_docker/nginx/frontends-v0-v1-proxy.conf` |
| T3 | Sprint 1 | BE | Completed | App Campo MVP router in `01_source/backend/runtime/app/routers/field_app.py` |
| T4 | Sprint 1 | BE | Completed | NOC MVP router in `01_source/backend/order_lifecycle_service/app/routers/noc.py` |
| T5 | Sprint 1 | BE | Completed | Suporte MVP routers in `01_source/order_pickup_service/app/routers/support.py` and `support_mvp.py` |
| T6 | Sprint 1 | FISC | Completed | Fiscal flags and pre-flight script in `02_docker/run_f3_preflight_mvp.sh` |
| T7 | Sprint 1 | QA | Completed | Smoke/E2E scripts and runbook templates created |
| T8 | Sprint 2 | FE | Completed | App Campo, NOC and Suporte frontend pages implemented |
| T9 | Sprint 2 | BE | Completed | App Campo status now reads runtime DB/registry |
| T10 | Sprint 2 | BE | Completed | NOC dashboard aggregates runtime, lifecycle and pickup data |
| T11 | Sprint 2 | BE | Completed | Suporte timeline reads order, lifecycle and fiscal sources |
| T12 | Sprint 2 | FE | Not Started | Pending definition/execution |
| T13 | Sprint 2 | QA | Not Started | Pending definition/execution |
| T14 | Sprint 3 | BE | Not Started | Pending definition/execution |
| T15 | Sprint 3 | FE+BE | Completed | App Campo offline queue with IndexedDB in `offlineStorage.ts` |
| T16 | Sprint 3 | BE | Completed | Fake NOC incident endpoint added |
| T17 | Sprint 3 | BE | Completed | Suporte escalation endpoint and `escalated_to` field added |
| T18 | Sprint 3 | QA | Not Started | Pending definition/execution |
| T19 | Sprint 3 | QA | Not Started | Pending definition/execution |
| T20 | Sprint 4 | FE | Not Started | Pending definition/execution |
| T21 | Sprint 4 | BE | Not Started | Pending definition/execution |
| T22 | Sprint 4 | FISC | Completed | Fiscal Go/No-Go script created in `02_docker/run_f3_go_no_go.sh` |
| T23 | Sprint 4 | FISC | Not Started | Pending definition/execution |
| T24 | Sprint 4 | QA | Completed | Final regression passed: `12/12` in `docs/regression_final_report.md` |
| T25 | Sprint 4 | PM | Not Started | Pending final closure / go-live sign-off |

## Risk Register
| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Proxy v0/v1 compose drift | Medium | Keep regression pointed to `localhost:5180` and validate `02_docker/docker-compose.frontends-v0-v1.yml` before release | FE+DevOps |
| Fiscal homologation delay | High | Keep stub/fallback path active and repeat `02_docker/run_f3_go_no_go.sh` after provider readiness | FISC |
| Frontend migration breaking legacy flows | High | Keep v0 fallback proxy and restrict v1 rollout to migrated routes | FE |
| Offline sync complexity | Medium | Keep manual sync MVP and add conflict/retry policy later | BE+FE |
| Support timeline depends on external fiscal/lifecycle availability | Medium | Preserve source-level degradation in payload and fallback to local fiscal documents | BE |

## Next Actions
1. @FE+DevOps: Keep proxy v0/v1 running on `http://localhost:5180/` during release validation.
2. @BE: Define and execute T12-T14/T18-T21 scope or explicitly cut from MVP.
3. @FISC: Confirm whether T23 is required for release or covered by T22 evidence.
4. @QA: Rerun regression after proxy fix and attach `docs/regression_final_report.md` as release evidence.
5. @PM: Convert T25 into final go-live sign-off once regression is green.
