"""
Framework leve para A/B testing e simulação de políticas (controle vs tratamento).

- Atribuição determinística por hash (estável por unidade).
- Simulação Monte Carlo de regret acumulado para comparar Thompson vs braço fixo.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

Variant = Literal["control", "treatment"]


def assign_ab_variant(unit_id: str, experiment_salt: str = "pricing_v1") -> Variant:
    """50/50 estável: mesmo unit_id + salt sempre retorna o mesmo braço."""
    h = hashlib.sha256(f"{experiment_salt}:{unit_id}".encode()).hexdigest()
    n = int(h[:8], 16)
    return "treatment" if (n % 2) == 0 else "control"


@dataclass
class SimulationResult:
    policy: str
    mean_cumulative_reward: float
    std_cumulative_reward: float
    mean_simple_regret: float


def simulate_policy_comparison(
    *,
    n_steps: int = 500,
    n_runs: int = 80,
    d: int = 10,
    k: int = 9,
    seed: int = 42,
    thompson_v: float = 0.35,
) -> dict[str, Any]:
    """
    Ambiente sintético: recompensa esperada linear por braço + ruído gaussiano.
    Compara:
    - `thompson`: amostragem ~ argmax w_a^T x (disjoint linear TS simplificado)
    - `fixed_arm`: sempre braço 4 (preço base)
    """
    rng_master = np.random.default_rng(seed)
    results: list[SimulationResult] = []

    def run_episode(policy: str) -> tuple[float, float]:
        rng = np.random.default_rng(int(rng_master.integers(1_000_000_000)))
        theta_true = [rng.standard_normal(d) for _ in range(k)]
        cum_r = 0.0
        opt_per_step: list[float] = []
        for _t in range(n_steps):
            x = rng.standard_normal(d)
            opt = max(float(theta_true[a] @ x) for a in range(k))
            opt_per_step.append(opt)
            if policy == "fixed_arm":
                arm = 4
            else:
                scores = []
                for a in range(k):
                    noise = thompson_v * rng.standard_normal(d)
                    w_hat = theta_true[a] + noise  # proxy de posterior ruidoso
                    scores.append(float(w_hat @ x))
                arm = int(np.argmax(scores))
            mean_r = float(theta_true[arm] @ x)
            cum_r += mean_r + 0.15 * rng.standard_normal()
        simple_regret = float(np.mean(opt_per_step) * n_steps - cum_r)
        return cum_r, simple_regret

    for policy in ("thompson", "fixed_arm"):
        crs: list[float] = []
        regs: list[float] = []
        for _ in range(n_runs):
            cr, reg = run_episode(policy)
            crs.append(cr)
            regs.append(reg)
        results.append(
            SimulationResult(
                policy=policy,
                mean_cumulative_reward=float(np.mean(crs)),
                std_cumulative_reward=float(np.std(crs)),
                mean_simple_regret=float(np.mean(regs)),
            )
        )

    lift = 0.0
    if len(results) == 2 and results[1].mean_cumulative_reward != 0:
        lift = (results[0].mean_cumulative_reward - results[1].mean_cumulative_reward) / max(
            1e-6, abs(results[1].mean_cumulative_reward)
        )

    return {
        "n_steps": n_steps,
        "n_runs": n_runs,
        "policies": [r.__dict__ for r in results],
        "relative_lift_thompson_vs_fixed": round(lift, 4),
    }


def experiment_record_template(
    experiment_id: str,
    variant: Variant,
    locker_id: str,
    product_id: str,
    arm_index: int | None,
    reward: float | None,
) -> dict[str, Any]:
    """Payload sugerido para append em fila/warehouse (contrato mínimo)."""
    return {
        "experiment_id": experiment_id,
        "variant": variant,
        "locker_id": locker_id,
        "product_id": product_id,
        "arm_index": arm_index,
        "reward": reward,
    }
