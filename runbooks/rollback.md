# Runbook — Rollback (< 1 min)

```bash
export USE_PARTNER_SERVICE=false
kubectl rollout undo deployment/order-pickup-service
```
