# Runbook — Reconciliação (dupla escrita / noturno)

1. Confirmar job noturno (inventory / wallet) com janela UTC acordada.
2. Comparar contagens: pedidos, reservas, saldos — threshold < 0.01% divergência.
3. Se divergência acima do SLO: pausar canário (`scripts/canary.sh` exit 2), abrir incidente.
4. Após correção: reexecutar `python scripts/baseline.py` e anexar JSON ao ticket.
