# Runbook — Incidente (erro > 0,5% / 5 min)

- Gatilho: `error_rate > 0.5%` por 5 minutos → alerta **PagerDuty** + **rollback automático** (`scripts/rollback.sh` / `runbooks/rollback.md`).
