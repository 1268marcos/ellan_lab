# Runbook — Incidente (alerta > 0.5% erro / 5 min)

1. Ack alerta no Pager/on-call.
2. Abrir dashboard `dashboards/migration.json` (Grafana).
3. Se erro > 0.5% por 5 min: executar `runbooks/rollback.md`.
4. Coletar `python scripts/baseline.py` antes/depois.
5. Post-mortem em 48h: causa raiz, ação preventiva.
