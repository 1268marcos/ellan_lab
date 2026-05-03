"""Predição LTV por cliente (BG/NBD + Gamma-Gamma) e materialização em customer_ltv_scores."""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import summary_data_from_transaction_data

from app import db
from app.config import settings
from app.ml_ltv.ltv_data import (
    load_features_90d_df,
    load_transactions_df,
    observation_period_end,
    user_consent_flags,
)

logger = logging.getLogger(__name__)

BUNDLE_NAME = "ltv_bgnbd_gamma_bundle.joblib"


def _bundle_path() -> Path:
    base = Path(settings.ltv_model_dir or settings.ml_model_dir or "./artifacts")
    return (base / BUNDLE_NAME).resolve()


def load_ltv_bundle() -> dict[str, Any]:
    path = _bundle_path()
    if not path.is_file():
        raise FileNotFoundError(f"LTV bundle missing: {path}")
    return joblib.load(path)


def _churn_30d_proxy(bgf: BetaGeoFitter, frequency: float, recency: float, T: float) -> tuple[float, float]:
    """P(alive) BG/NBD e proxy de 'sem recompra em 30d' via Poisson(lambda=E[N])."""
    f, r, t = float(frequency), float(recency), float(T)
    p_alive = float(np.asarray(bgf.conditional_probability_alive(f, r, t), dtype=float).ravel()[0])
    p_alive = float(np.clip(p_alive, 0.0, 1.0))
    lam = float(np.asarray(bgf.conditional_expected_number_of_purchases_up_to_time(30.0, f, r, t), dtype=float).ravel()[0])
    lam = max(lam, 0.0)
    prob_no_rep = float(math.exp(-min(lam, 50.0)))
    churn_probability_30d = float(np.clip(prob_no_rep, 0.0, 1.0))
    return churn_probability_30d, p_alive


def _approximate_ltv_quantiles_mle_bayes(
    bgf: BetaGeoFitter,
    ggf: GammaGammaFitter,
    frequency: float,
    recency: float,
    T: float,
    monetary_value: float,
    sigma_lognormal: float,
    n_samples: int = 800,
    rng: np.random.Generator | None = None,
) -> tuple[float, float]:
    """
    Incerteza epistêmica aproximada: amostragem dos coeficientes ~ Normal(MLE, SE)
    (inferência asintótica / Laplace) e propagação para CLV 12m em centavos.
    """
    rng = rng or np.random.default_rng(42)
    clv_samples: list[float] = []
    n_ok = 0
    for _ in range(n_samples * 2):
        if n_ok >= n_samples:
            break
        try:
            rp = {}
            for name in bgf.params_.index:
                mu = float(bgf.params_[name])
                se = float(bgf.standard_errors_.get(name, mu * 0.08 + 1e-6))
                rp[name] = max(1e-8, rng.normal(mu, se))
            qp = {}
            for name in ggf.params_.index:
                mu = float(ggf.params_[name])
                se = float(ggf.standard_errors_.get(name, mu * 0.08 + 1e-6))
                qp[name] = max(1e-8, rng.normal(mu, se))
            bg = BetaGeoFitter(penalizer_coef=0.0)
            bg.params_ = pd.Series(rp)
            bg._scale = bgf._scale  # type: ignore[attr-defined]
            gg = GammaGammaFitter(penalizer_coef=0.0)
            gg.params_ = pd.Series(qp)
            raw = gg.customer_lifetime_value(
                bg,
                frequency=pd.Series([frequency], dtype=float),
                recency=pd.Series([recency], dtype=float),
                T=pd.Series([T], dtype=float),
                monetary_value=pd.Series([max(monetary_value, 1e-6)], dtype=float),
                time=12,
                discount_rate=0.0,
                freq="D",
            )
            v = float(raw.iloc[0]) if hasattr(raw, "iloc") else float(raw[0])
            if not math.isfinite(v) or v < 0:
                continue
            noise = rng.normal(0.0, max(sigma_lognormal, 0.05))
            clv_samples.append(max(0.0, v * math.exp(noise)) * 100.0)
            n_ok += 1
        except Exception:
            continue
    if len(clv_samples) < 50:
        point = _point_clv_cents(bgf, ggf, frequency, recency, T, monetary_value)
        return float(point * 0.8), float(point * 1.2)
    lo, hi = np.quantile(clv_samples, [0.05, 0.95])
    return float(lo), float(hi)


def _point_clv_cents(
    bgf: BetaGeoFitter,
    ggf: GammaGammaFitter,
    frequency: float,
    recency: float,
    T: float,
    monetary_value: float,
) -> float:
    raw = ggf.customer_lifetime_value(
        bgf,
        frequency=pd.Series([frequency], dtype=float),
        recency=pd.Series([recency], dtype=float),
        T=pd.Series([T], dtype=float),
        monetary_value=pd.Series([max(monetary_value, 1e-6)], dtype=float),
        time=12,
        discount_rate=0.0,
        freq="D",
    )
    v = float(raw.iloc[0]) if hasattr(raw, "iloc") else float(raw[0])
    return max(0.0, v * 100.0)


def _segment_from_tertiles(ltv_cents: float, t33: float, t66: float) -> str:
    if ltv_cents >= t66:
        return "High Value"
    if ltv_cents >= t33:
        return "Medium Value"
    return "Low Value"


def _campaign_segment(seg: str, consent_marketing: bool, consent_analytics: bool) -> str:
    parts = [seg.upper().replace(" ", "_")]
    if consent_marketing:
        parts.append("MKT_OK")
    else:
        parts.append("MKT_OFF")
    if consent_analytics:
        parts.append("ANALYTICS_OK")
    else:
        parts.append("ANALYTICS_OFF")
    return "|".join(parts)


def build_summary_for_users(customer_ids: set[str] | None = None) -> pd.DataFrame:
    """Resumo RFM (lifetimes) a partir do histórico completo de transações."""
    trans = load_transactions_df()
    if trans.empty:
        raise RuntimeError("sem transações para LTV")
    if customer_ids is not None:
        trans = trans[trans["customer_id"].isin(customer_ids)]
        if trans.empty:
            raise RuntimeError("nenhuma transação para os usuários solicitados")
    obs_end = observation_period_end()
    summary = summary_data_from_transaction_data(
        trans,
        customer_id_col="customer_id",
        datetime_col="datetime",
        monetary_value_col="monetary_value",
        observation_period_end=obs_end,
        freq="D",
    )
    summary = summary.reset_index().rename(columns={"customer_id": "user_id"})
    return summary


def predict_row_from_summary(
    bundle: dict[str, Any],
    row: pd.Series,
    tertiles: tuple[float, float],
    sigma_lognormal: float,
) -> dict[str, Any]:
    bgf: BetaGeoFitter = bundle["bgf"]
    ggf: GammaGammaFitter = bundle["ggf"]
    f = float(row["frequency"])
    r = float(row["recency"])
    t = float(row["T"])
    m = float(row.get("monetary_value") or 0.0)
    if m <= 0:
        m = float(bundle.get("population_mean_monetary", 1.0))
    ltv_cents = _point_clv_cents(bgf, ggf, f, r, t, m)
    churn_30d, p_alive = _churn_30d_proxy(bgf, f, r, t)
    t33, t66 = tertiles
    seg = _segment_from_tertiles(ltv_cents, t33, t66)
    p05, p95 = _approximate_ltv_quantiles_mle_bayes(bgf, ggf, f, r, t, m, sigma_lognormal)
    p05_cents = int(max(0, round(min(p05, ltv_cents))))
    p95_cents = int(max(0, round(max(p95, ltv_cents))))
    return {
        "predicted_ltv_12m_cents": int(round(ltv_cents)),
        "ltv_p05_cents": p05_cents,
        "ltv_p95_cents": p95_cents,
        "churn_probability_30d": round(churn_30d, 6),
        "p_alive": round(p_alive, 6),
        "segmento_cliente": seg,
        "frequency": f,
        "recency_days": r,
        "T_days": t,
        "monetary_value_avg": m,
    }


def score_all_customers_and_upsert() -> dict[str, Any]:
    """Recalcula scores para todos os usuários com histórico e grava customer_ltv_scores."""
    bundle = load_ltv_bundle()
    summary = build_summary_for_users()
    feats = load_features_90d_df()
    if not feats.empty:
        feats = feats.set_index("user_id", drop=False)
    # Tercis globais para segmentação estável nesta execução
    bgf: BetaGeoFitter = bundle["bgf"]
    ggf: GammaGammaFitter = bundle["ggf"]
    sigma_ln = float(bundle.get("sigma_lognormal_clv", 0.18))
    ltvs = []
    for _, row in summary.iterrows():
        ltvs.append(_point_clv_cents(bgf, ggf, float(row["frequency"]), float(row["recency"]), float(row["T"]), float(row.get("monetary_value") or 1.0)))
    t33, t66 = np.quantile(ltvs, [1 / 3, 2 / 3]) if ltvs else (0.0, 0.0)
    tertiles = (float(t33), float(t66))
    mv = datetime.now(timezone.utc)
    version = str(bundle.get("model_version", "unknown"))
    n = 0
    for _, row in summary.iterrows():
        uid = str(row["user_id"])
        pred = predict_row_from_summary(bundle, row, tertiles, sigma_ln)
        fr = feats.loc[uid] if uid in feats.index else {}
        if isinstance(fr, pd.DataFrame):
            fr = fr.iloc[0]
        consent_a = bool(fr.get("consent_analytics", False)) if len(fr) else False
        consent_m = bool(fr.get("consent_marketing", False)) if len(fr) else False
        campaign = _campaign_segment(pred["segmento_cliente"], consent_m, consent_a)
        feature_blob = {
            "total_gasto_cents": int(fr.get("total_gasto_cents", 0) or 0),
            "frequencia_compras": int(fr.get("frequencia_compras", 0) or 0),
            "recencia_ultima_compra_dias": fr.get("recencia_ultima_compra_dias"),
            "ticket_medio_cents": float(fr.get("ticket_medio_cents", 0) or 0),
            "canais_utilizados": {
                "online": bool(fr.get("used_online", False)),
                "kiosk": bool(fr.get("used_kiosk", False)),
            },
            "produtos_categoria_preferida": str(fr.get("produtos_categoria_preferida", "")),
            "horario_preferido_compras": int(fr.get("horario_preferido_compras", 0) or 0),
            "country_code": fr.get("country_code"),
            "region": fr.get("region"),
            "notification_engagement_90d": int(fr.get("notification_engagement_90d", 0) or 0),
        }
        db.execute(
            """
            INSERT INTO customer_ltv_scores (
                user_id, predicted_ltv_12m_cents, ltv_p05_cents, ltv_p95_cents,
                churn_probability_30d, p_alive, segmento_cliente, campaign_segment,
                features_90d, notification_engagement_90d, consent_analytics, consent_marketing,
                model_version, scored_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id) DO UPDATE SET
                predicted_ltv_12m_cents = EXCLUDED.predicted_ltv_12m_cents,
                ltv_p05_cents = EXCLUDED.ltv_p05_cents,
                ltv_p95_cents = EXCLUDED.ltv_p95_cents,
                churn_probability_30d = EXCLUDED.churn_probability_30d,
                p_alive = EXCLUDED.p_alive,
                segmento_cliente = EXCLUDED.segmento_cliente,
                campaign_segment = EXCLUDED.campaign_segment,
                features_90d = EXCLUDED.features_90d,
                notification_engagement_90d = EXCLUDED.notification_engagement_90d,
                consent_analytics = EXCLUDED.consent_analytics,
                consent_marketing = EXCLUDED.consent_marketing,
                model_version = EXCLUDED.model_version,
                scored_at = EXCLUDED.scored_at
            """,
            (
                uid,
                pred["predicted_ltv_12m_cents"],
                pred["ltv_p05_cents"],
                pred["ltv_p95_cents"],
                pred["churn_probability_30d"],
                pred["p_alive"],
                pred["segmento_cliente"],
                campaign,
                json.dumps(feature_blob, default=str),
                int(fr.get("notification_engagement_90d", 0) or 0),
                consent_a,
                consent_m,
                version,
                mv,
            ),
        )
        n += 1
    logger.info("customer_ltv_scores upserted rows=%s version=%s", n, version)
    return {"rows_upserted": n, "model_version": version, "tertiles_cents": tertiles}


def predict_customer_ltv_payload(user_id: str, require_consent: bool = True) -> dict[str, Any]:
    """Predição on-the-fly + metadados (para GET /customers/{id}/ltv)."""
    consents = user_consent_flags(user_id)
    if require_consent and not consents["consent_analytics"]:
        raise PermissionError("Consentimento ANALYTICS necessário para LTV preditivo")
    bundle = load_ltv_bundle()
    summary = build_summary_for_users({user_id})
    if summary.empty:
        raise ValueError("Cliente sem histórico de compras pago")
    row = summary.iloc[0]
    sigma_ln = float(bundle.get("sigma_lognormal_clv", 0.18))
    # tercis do bundle materializado ou recalculados mínimos
    tertiles = tuple(bundle.get("tertiles_cents", (0.0, 1.0)))  # type: ignore[arg-type]
    pred = predict_row_from_summary(bundle, row, tertiles, sigma_ln)
    feats = load_features_90d_df()
    fr = feats[feats["user_id"] == user_id]
    frd = fr.iloc[0].to_dict() if not fr.empty else {}
    campaign = _campaign_segment(pred["segmento_cliente"], consents["consent_marketing"], consents["consent_analytics"])
    out = {
        "user_id": user_id,
        "predicted_ltv_12m_cents": pred["predicted_ltv_12m_cents"],
        "ltv_credible_interval_90_cents": {"low": pred["ltv_p05_cents"], "high": pred["ltv_p95_cents"]},
        "churn_probability_30d": pred["churn_probability_30d"],
        "p_alive_bgnbd": pred["p_alive"],
        "segmento_cliente": pred["segmento_cliente"],
        "campaign_segment": campaign,
        "model_version": bundle.get("model_version"),
        "inference": "BG/NBD + Gamma-Gamma (lifetimes); intervalos por propagação assintótica + ruído lognormal empírico",
        "features_90d": {
            "total_gasto_cents": int(frd.get("total_gasto_cents", 0) or 0),
            "frequencia_compras": int(frd.get("frequencia_compras", 0) or 0),
            "recencia_ultima_compra_dias": frd.get("recencia_ultima_compra_dias"),
            "ticket_medio_cents": float(frd.get("ticket_medio_cents", 0) or 0),
            "canais_utilizados": {"online": bool(frd.get("used_online")), "kiosk": bool(frd.get("used_kiosk"))},
            "produtos_categoria_preferida": frd.get("produtos_categoria_preferida"),
            "horario_preferido_compras": frd.get("horario_preferido_compras"),
            "country_code": frd.get("country_code"),
            "region": frd.get("region"),
            "notification_engagement_90d": int(frd.get("notification_engagement_90d", 0) or 0),
        },
        "consents": consents,
    }
    return out
