# Runbook — Rollback (flags < 1 min)

1. Definir env no `order_pickup_service` (ou secret/compose):
   - `USE_PARTNER_SERVICE=false`
   - `USE_INVENTORY_SERVICE=false`
   - `USE_WALLET_SERVICE=false`
   - `USE_LOGISTICS_SERVICE=false`
   - `SHADOW_MODE_ENABLED=false`
2. Reiniciar pods/containers do monólito.
3. Verificar `GET /health/ready` e tráfego v1.
4. Registrar incidente (link `runbooks/incident.md`).
