from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.bi_core import AnalyticsFact, BiKpiDefinition, BiReportCatalog
from app.models.bi_partners import BiDataPartner
from app.schemas.partner import WebhookConfigureIn
from app.services import (
    bi_efficiency_service,
    bi_integrations_service,
    bi_marts_service,
    bi_ops_service,
    bi_players_service,
    partner_service,
)
from app.services.crypto_util import new_id

KPI_SEEDS = [
    ("LOCKER_FILL_RATE", "Taxa de ocupacao locker", "LOCKER", "DAILY", "ml_features_daily"),
    ("PARTNER_MRR", "MRR por parceiro", "FINANCE", "MONTHLY", "company_mrr_trend"),
    ("LOCKER_GROSS_MARGIN", "Margem bruta locker", "FINANCE", "MONTHLY", "locker_pnl"),
    ("PICKUP_SLA", "SLA retirada", "LOGISTICS", "DAILY", "analytics_facts"),
    ("NETWORK_UPTIME", "Uptime rede", "LOCKER", "DAILY", "ml_features_daily"),
]

REPORT_SEEDS = [
    ("OPS_LOCKER_EXEC", "Executive Locker OPS", "DASHBOARD"),
    ("CFO_MRR_TREND", "MRR & deferred revenue", "DASHBOARD"),
    ("PARTNER_PNL", "Locker P&L por parceiro", "DASHBOARD"),
]


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "partners": 0,
        "facts": 0,
        "kpis": 0,
        "reports": 0,
        "mrr": 0,
        "players": 0,
    }

    if not db.query(BiDataPartner).filter(BiDataPartner.code == "BI-WAREHOUSE-BR").first():
        pid = new_id()
        db.add(
            BiDataPartner(
                id=pid,
                name="Data Warehouse Brasil",
                code="BI-WAREHOUSE-BR",
                partner_type="WAREHOUSE",
                region_code="BR",
                api_base_url="https://bi.example/warehouse",
                active=True,
            )
        )
        db.flush()
        counts["partners"] += 1
        partner_service.configure_webhook(
            db,
            pid,
            WebhookConfigureIn(
                url="https://hooks.example/bi/warehouse",
                secret="whsec_bi_demo",
                events=["fact.ingested", "mart.refreshed"],
            ),
        )
        partner_service.rotate_api_key(db, pid, rotated_by="seed")

    for code, name, domain, grain, table in KPI_SEEDS:
        if not db.query(BiKpiDefinition).filter(BiKpiDefinition.code == code).first():
            db.add(
                BiKpiDefinition(
                    id=new_id(),
                    code=code,
                    name=name,
                    domain=domain,
                    grain=grain,
                    source_table=table,
                    formula_hint=f"SELECT * FROM {table}",
                )
            )
            counts["kpis"] += 1

    for code, name, rtype in REPORT_SEEDS:
        if not db.query(BiReportCatalog).filter(BiReportCatalog.code == code).first():
            db.add(
                BiReportCatalog(
                    id=new_id(),
                    code=code,
                    name=name,
                    report_type=rtype,
                    tags_json=json.dumps(["ops", "locker", "finance"]),
                )
            )
            counts["reports"] += 1

    now = datetime.now(timezone.utc)
    if not db.query(AnalyticsFact).first():
        db.add(
            AnalyticsFact(
                id=uuid.uuid4(),
                fact_key="seed.pickup.completed",
                fact_name="pickup_completed",
                order_id="ord-seed-001",
                order_channel="MARKETPLACE",
                region_code="BR-SP",
                payload=json.dumps({"locker_id": "lck-demo", "duration_sec": 42}),
                occurred_at=now - timedelta(hours=2),
                created_at=now,
            )
        )
        counts["facts"] += 1

    from app.models.bi_marts import CompanyMrrTrend

    month = date.today().replace(day=1)
    if not db.query(CompanyMrrTrend).first():
        bi_marts_service.upsert_mrr(db, month, "BRL", 125000000, 42, 1280)
        counts["mrr"] += 1

    player_seed = bi_players_service.seed_players(db)
    counts["players"] = player_seed.get("players_inserted", 0)
    counts["players_updated"] = player_seed.get("players_updated", 0)
    counts["tier1_coverage"] = player_seed.get("tier1_present", 0)

    prof = bi_ops_service.seed_taxonomy_and_lineage(db)
    counts.update({f"prof_{k}": v for k, v in prof.items()})
    counts["market_presence"] = bi_ops_service.seed_market_presence(db)
    counts["readiness"] = bi_ops_service.recompute_all_readiness(db)
    integ = bi_integrations_service.seed_integrations(db)
    counts.update({f"integration_{k}": v for k, v in integ.items()})
    eff = bi_efficiency_service.seed_efficiency(db)
    counts.update({f"efficiency_{k}": v for k, v in eff.items()})

    db.commit()
    return counts
