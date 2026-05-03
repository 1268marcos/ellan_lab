"""Treina BG/NBD + Gamma-Gamma (lifetimes), persiste bundle e opcionalmente materializa customer_ltv_scores."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import summary_data_from_transaction_data

from app.config import settings
from app.ml_ltv.ltv_data import load_transactions_df, observation_period_end
from app.ml_ltv.predict_customer_ltv import BUNDLE_NAME, _point_clv_cents, score_all_customers_and_upsert

logger = logging.getLogger(__name__)


def _artifact_dir() -> Path:
    return Path(settings.ltv_model_dir or settings.ml_model_dir or "./artifacts").resolve()


def train_and_save_bundle(
    penalizer_bg: float = 0.01,
    penalizer_gg: float = 0.01,
) -> dict:
    trans = load_transactions_df()
    if len(trans) < 40:
        raise RuntimeError(f"poucas linhas de transação para treino BG/NBD: {len(trans)} (mínimo 40)")
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
    freq = summary["frequency"].values
    rec = summary["recency"].values
    T = summary["T"].values
    monetary = summary["monetary_value"].values.astype(float)

    bgf = BetaGeoFitter(penalizer_coef=penalizer_bg)
    bgf.fit(freq, rec, T, verbose=False)

    mask = summary["frequency"] > 0
    if mask.sum() < 30:
        raise RuntimeError(f"poucos clientes com recompra para Gamma-Gamma: {int(mask.sum())}")
    ggf = GammaGammaFitter(penalizer_coef=penalizer_gg)
    ggf.fit(summary.loc[mask, "frequency"].values, summary.loc[mask, "monetary_value"].values, verbose=False)

    pop_m = float(np.mean(summary.loc[mask, "monetary_value"]))

    ltvs = []
    for _, row in summary.iterrows():
        m = float(row["monetary_value"]) if float(row["monetary_value"]) > 0 else pop_m
        ltvs.append(_point_clv_cents(bgf, ggf, float(row["frequency"]), float(row["recency"]), float(row["T"]), m))
    sigma_ln = float(np.std(np.log(np.maximum(np.array(ltvs), 1.0)))) if ltvs else 0.18
    sigma_ln = max(0.08, min(sigma_ln, 0.6))
    t33, t66 = np.quantile(ltvs, [1 / 3, 2 / 3]) if ltvs else (0.0, 1.0)
    tertiles = (float(t33), float(t66))

    version = f"ltv_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    bundle = {
        "bgf": bgf,
        "ggf": ggf,
        "model_version": version,
        "observation_period_end": obs_end.isoformat(),
        "n_customers": int(len(summary)),
        "n_transactions": int(len(trans)),
        "population_mean_monetary": pop_m,
        "sigma_lognormal_clv": sigma_ln,
        "tertiles_cents": tertiles,
        "metrics": {
            "n_returning_customers": int(mask.sum()),
        },
    }
    out_dir = _artifact_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / BUNDLE_NAME
    joblib.dump(bundle, path)
    (out_dir / "ltv_bundle.meta.json").write_text(
        json.dumps(
            {
                "model_version": version,
                "path": str(path),
                "n_customers": len(summary),
                "sigma_lognormal_clv": sigma_ln,
                "tertiles_cents": tertiles,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("LTV bundle saved path=%s customers=%s", path, len(summary))
    return {"path": str(path), "model_version": version, "n_customers": len(summary), "tertiles_cents": tertiles}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(description="Treina LTV BG/NBD + Gamma-Gamma")
    p.add_argument("--materialize", action="store_true", help="Após treinar, preenche customer_ltv_scores")
    args = p.parse_args()
    out = train_and_save_bundle()
    print(json.dumps(out, indent=2))
    if args.materialize:
        up = score_all_customers_and_upsert()
        print(json.dumps(up, indent=2))


if __name__ == "__main__":
    main()
