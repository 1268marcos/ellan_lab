"""
Bandit contextual (modelos lineares disjuntos + Thompson Sampling) para ajuste de preço.

Braços: multiplicadores discretos equivalentes a -15% … +25% (passo 5%).
Recompensa alvo (para updates explícitos): proxy de receita ou conversão observada.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.config import settings
from app.ml_pricing.context_features import (
    PricingContextRaw,
    context_to_vector,
    fetch_active_bundle_for_product,
    load_pricing_context,
)
from app.ml_pricing.elasticity_model import demand_multiplier, revenue_proxy_cents

logger = logging.getLogger(__name__)

# Ajuste relativo ao preço base: -15% .. +25% em passos de 5%
ARM_PRICE_DELTAS: list[float] = [-0.15 + 0.05 * i for i in range(9)]
K_ARMS = len(ARM_PRICE_DELTAS)
LAMBDA_RIDGE = 1.0
TS_NOISE = 0.35  # v em v^2 (A^{-1}) — exploração


def _default_baseline_vector(d: int) -> np.ndarray:
    """Referência SHAP (mercado típico) alinhada ao encoding de context_to_vector."""
    b = np.zeros(d, dtype=np.float64)
    if d > 0:
        b[0] = 1.0
    if d > 6:
        b[6] = 0.45  # ocupação
    if d > 7:
        b[7] = float(np.log1p(5.0))  # log dist
    if d > 8:
        b[8] = 0.5  # temp norm
    if d > 9:
        b[9] = -1.0  # elasticidade típica
    return b


def linear_shap_attributions(
    w: np.ndarray,
    x: np.ndarray,
    baseline: np.ndarray,
    feature_names: list[str],
) -> dict[str, Any]:
    """
    Valores SHAP exatos para f(x)=w^T x (modelo linear) com baseline explícito:
    phi_j = w_j * (x_j - r_j), soma = f(x) - f(r).
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    w = np.asarray(w, dtype=np.float64).ravel()
    baseline = np.asarray(baseline, dtype=np.float64).ravel()
    contrib = w * (x - baseline)
    out = {feature_names[i]: float(contrib[i]) for i in range(min(len(contrib), len(feature_names)))}
    return {
        "method": "linear_shap_exact",
        "feature_values": out,
        "prediction_delta": float(contrib.sum()),
        "f_x": float(w @ x),
        "f_baseline": float(w @ baseline),
    }


class DisjointLinearThompsonBandit:
    """Um modelo linear Ridge por braço; Thompson Sampling para escolha."""

    def __init__(self, d: int, k: int = K_ARMS, lam: float = LAMBDA_RIDGE, v: float = TS_NOISE):
        self.d = d
        self.k = k
        self.lam = lam
        self.v = v
        self.A = [lam * np.eye(d, dtype=np.float64) for _ in range(k)]
        self.b = [np.zeros(d, dtype=np.float64) for _ in range(k)]

    def observe(self, arm: int, x: np.ndarray, reward: float) -> None:
        arm = int(arm)
        if arm < 0 or arm >= self.k:
            raise ValueError("arm out of range")
        x = np.asarray(x, dtype=np.float64).ravel()
        if x.shape[0] != self.d:
            raise ValueError("dim mismatch")
        self.A[arm] += np.outer(x, x)
        self.b[arm] += reward * x

    def posterior_mean(self, arm: int) -> np.ndarray:
        A = self.A[arm]
        return np.linalg.solve(A + 1e-9 * np.eye(self.d), self.b[arm])

    def sample_score(self, arm: int, x: np.ndarray, rng: np.random.Generator) -> float:
        A = self.A[arm]
        mu = np.linalg.solve(A + 1e-9 * np.eye(self.d), self.b[arm])
        try:
            cov = (self.v**2) * np.linalg.inv(A + 1e-6 * np.eye(self.d))
            L = np.linalg.cholesky(cov + 1e-5 * np.eye(self.d))
            w = mu + L @ rng.standard_normal(self.d)
        except np.linalg.LinAlgError:
            w = mu + self.v * rng.standard_normal(self.d) * 0.1
        return float(w @ x)

    def to_dict(self) -> dict[str, Any]:
        return {
            "d": self.d,
            "k": self.k,
            "lam": self.lam,
            "v": self.v,
            "A": [a.tolist() for a in self.A],
            "b": [b.tolist() for b in self.b],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DisjointLinearThompsonBandit:
        out = cls(d=int(d["d"]), k=int(d["k"]), lam=float(d.get("lam", LAMBDA_RIDGE)), v=float(d.get("v", TS_NOISE)))
        out.A = [np.array(m, dtype=np.float64) for m in d["A"]]
        out.b = [np.array(v, dtype=np.float64) for v in d["b"]]
        return out


def _state_path() -> Path:
    return Path(settings.pricing_bandit_state_path)


def load_bandit(d: int) -> DisjointLinearThompsonBandit:
    p = _state_path()
    if p.exists():
        try:
            raw = joblib.load(p)
            if isinstance(raw, DisjointLinearThompsonBandit):
                return raw
            if isinstance(raw, dict) and int(raw.get("d", -1)) == d:
                return DisjointLinearThompsonBandit.from_dict(raw)
        except Exception as exc:
            logger.warning("bandit state corrupt, reset: %s", exc)
    return DisjointLinearThompsonBandit(d=d, k=K_ARMS)


def save_bandit(b: DisjointLinearThompsonBandit) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(b.to_dict(), p)


def suggest_dynamic_pricing(
    locker_id: str,
    product_id: str,
    *,
    rng: np.random.Generator | None = None,
    persist_state: bool = False,
    apply_proxy_learning: bool = False,
) -> dict[str, Any]:
    """
    Retorna sugestão de preço, desconto, bundle e explainability (SHAP linear exato).
    `product_id` = SKU do catálogo.
    """
    rng = rng or np.random.default_rng()
    ctx: PricingContextRaw = load_pricing_context(locker_id, product_id)
    names, vals = context_to_vector(ctx)
    x = np.array(vals, dtype=np.float64)
    d = x.shape[0]
    bandit = load_bandit(d)

    scores = [bandit.sample_score(k, x, rng) for k in range(K_ARMS)]
    best = int(np.argmax(scores))
    delta = ARM_PRICE_DELTAS[best]
    mult = 1.0 + delta

    base = max(1, int(ctx.base_price_cents))
    suggested_cents = int(round(base * mult))

    # Desconto explícito para liberar estoque: maior quando ocupação alta (preço promocional agressivo)
    stock_pressure = float(ctx.occupancy_ratio)
    discount_clear_stock = min(25.0, max(0.0, 8.0 + 22.0 * stock_pressure + 5.0 * max(0.0, -ctx.historical_elasticity)))

    w_mean = bandit.posterior_mean(best)
    baseline = _default_baseline_vector(d)
    shap_exact = linear_shap_attributions(w_mean, x, baseline, names)

    bundle = fetch_active_bundle_for_product(product_id)
    bundle_out = None
    if bundle:
        bundle_out = {
            "bundle_id": bundle.get("id"),
            "name": bundle.get("name"),
            "code": bundle.get("code"),
            "amount_cents": int(bundle.get("amount_cents") or 0),
            "currency": bundle.get("currency") or "BRL",
        }

    proxy_rev = revenue_proxy_cents(base, delta, ctx.historical_elasticity)
    demand_m = demand_multiplier(ctx.historical_elasticity, delta)

    if apply_proxy_learning:
        # Recompensa em escala estável para Ridge online
        r = float(np.log1p(max(0.0, proxy_rev / 1000.0)))
        bandit.observe(best, x, r)
        if persist_state:
            save_bandit(bandit)

    return {
        "locker_id": locker_id,
        "product_id": product_id,
        "context": {
            "hour": ctx.hour,
            "dow": ctx.dow,
            "is_holiday": bool(ctx.is_holiday),
            "occupancy_ratio": round(ctx.occupancy_ratio, 4),
            "dist_competitor_km": round(ctx.dist_competitor_km, 3),
            "temp_season_norm": round(ctx.temp_season_norm, 4),
            "historical_elasticity": round(ctx.historical_elasticity, 4),
            "base_price_cents": base,
            "region": ctx.region,
        },
        "feature_vector": dict(zip(names, [round(v, 6) for v in vals])),
        "suggested_price_adjust_pct": round(delta * 100.0, 2),
        "suggested_price_multiplier": round(mult, 4),
        "suggested_unit_amount_cents": suggested_cents,
        "recommended_discount_pct_clear_stock": round(discount_clear_stock, 2),
        "bundle_recommendation": bundle_out,
        "arm_index": best,
        "thompson_sampled_scores": [round(float(s), 4) for s in scores],
        "revenue_proxy_cents": round(proxy_rev, 2),
        "demand_multiplier_proxy": round(demand_m, 4),
        "explainability": {
            "linear_shap": shap_exact,
            "note": "SHAP exato para score linear w^T x do braço escolhido (posterior mean).",
        },
    }


def bandit_feedback(locker_id: str, product_id: str, arm_index: int, reward: float, persist: bool = True) -> dict[str, Any]:
    """Atualiza posteriores após outcome real (ex.: conversão ou receita observada)."""
    ctx = load_pricing_context(locker_id, product_id)
    _, vals = context_to_vector(ctx)
    x = np.array(vals, dtype=np.float64)
    bandit = load_bandit(x.shape[0])
    bandit.observe(int(arm_index), x, float(reward))
    if persist:
        save_bandit(bandit)
    return {"ok": True, "locker_id": locker_id, "product_id": product_id, "arm_index": int(arm_index)}
