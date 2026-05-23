from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.privacy import (
    DataDeletionRequest,
    DataSubjectRequest,
    PrivacyConsent,
    PrivacyPolicyVersion,
    PrivacyRegulation,
)
from app.models.privacy_extended import (
    PrivacyBreachIncident,
    PrivacyDataCategory,
    PrivacyImpactAssessment,
    PrivacyLegalBasis,
    PrivacyProcessingActivity,
    PrivacyProcessor,
    PrivacyProcessorAgreement,
    PrivacyRetentionRule,
    PrivacyTransferRecord,
)
from app.models.privacy_pro import PrivacyComplianceSnapshot
from app.schemas.privacy_pro import ComplianceCompareOut, ComplianceDimensionOut, ComplianceScoreOut
from app.services.crypto_util import new_id, utcnow
from app.services.privacy_regulatory_service import obligations_score_for_regulation


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute_compliance_score(db: Session, regulation_code: str, *, persist: bool = True) -> ComplianceScoreOut:
    code = regulation_code.upper()
    reg = db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code).first()
    if not reg:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")

    policy_ok = (
        db.query(PrivacyPolicyVersion)
        .filter(PrivacyPolicyVersion.regulation_id == reg.id, PrivacyPolicyVersion.is_current.is_(True))
        .count()
        > 0
    )
    legal_bases = db.query(PrivacyLegalBasis).filter_by(regulation_code=code, active=True).count()
    ropa = db.query(PrivacyProcessingActivity).filter_by(regulation_code=code).count()
    processors = sum(1 for p in db.query(PrivacyProcessor).all() if code in json.loads(p.regulation_codes_json or "[]"))
    dpas = db.query(PrivacyProcessorAgreement).filter_by(regulation_code=code, status="ACTIVE").count()
    retention = db.query(PrivacyRetentionRule).filter_by(regulation_code=code, active=True).count()
    categories = db.query(PrivacyDataCategory).filter_by(regulation_code=code, active=True).count()
    dpia_done = (
        db.query(PrivacyImpactAssessment)
        .filter(PrivacyImpactAssessment.regulation_code == code, PrivacyImpactAssessment.status == "APPROVED")
        .count()
    )
    transfers = db.query(PrivacyTransferRecord).filter_by(regulation_code=code, status="ACTIVE").count()
    open_breaches = db.query(PrivacyBreachIncident).filter_by(regulation_code=code, status="OPEN").count()
    pending_dsar = db.query(DataSubjectRequest).filter_by(regulation_code=code, status="PENDING").count()
    pending_del = db.query(DataDeletionRequest).filter_by(regulation_code=code, status="PENDING").count()
    consents = db.query(PrivacyConsent).filter_by(regulation_code=code).count()
    reg_obl_score, reg_obl_detail = obligations_score_for_regulation(db, code)
    reg_obl_status = "OK" if reg_obl_score >= 80 else ("WARN" if reg_obl_score >= 50 else "GAP")

    dims: list[tuple[str, str, float, float, str, str]] = [
        ("policy", "Politica vigente", 10, 100.0 if policy_ok else 0.0, "OK" if policy_ok else "GAP", "Politica publicada e marcada como atual"),
        ("legal_bases", "Bases legais", 10, min(100.0, legal_bases * 20), "OK" if legal_bases >= 3 else "GAP", f"{legal_bases} bases catalogadas"),
        ("ropa", "ROPA Art. 30", 15, min(100.0, ropa * 25), "OK" if ropa >= 2 else "GAP", f"{ropa} atividades de tratamento"),
        ("processors", "Processadores + DPA", 15, min(100.0, (dpas / max(processors, 1)) * 100) if processors else 0.0, "OK" if processors and dpas >= processors else "GAP", f"{processors} processadores, {dpas} DPA ativos"),
        ("retention", "Retencao", 10, min(100.0, retention * 25), "OK" if retention >= 2 else "GAP", f"{retention} regras ativas"),
        ("categories", "Categorias dados", 5, min(100.0, categories * 20), "OK" if categories >= 3 else "GAP", f"{categories} categorias"),
        ("dpia", "DPIA/LIA", 10, 100.0 if dpia_done >= 1 else 0.0, "OK" if dpia_done else "GAP", f"{dpia_done} avaliacoes aprovadas"),
        ("transfers", "Transferencias", 5, min(100.0, transfers * 50) if transfers else 50.0, "OK" if transfers else "WARN", f"{transfers} registros ativos"),
        ("breaches", "Incidentes abertos", 10, 0.0 if open_breaches else 100.0, "GAP" if open_breaches else "OK", f"{open_breaches} incidentes abertos"),
        ("dsar_sla", "DSAR / eliminacao", 10, 100.0 if pending_dsar + pending_del == 0 else max(0.0, 100 - (pending_dsar + pending_del) * 25), "OK" if pending_dsar + pending_del == 0 else "WARN", f"{pending_dsar} DSAR + {pending_del} eliminacoes pendentes"),
        ("regulatory", "Obrigacoes regulatorias", 10, reg_obl_score, reg_obl_status, reg_obl_detail),
        ("consents", "Consentimentos", 5, min(100.0, consents * 10) if consents else 0.0, "OK" if consents >= 5 else "GAP", f"{consents} registros de consentimento"),
    ]

    weighted = sum(w * s / 100 for _, _, w, s, _, _ in dims)
    gaps = [f"{label}: {detail}" for _, label, _, score, st, detail in dims if st in ("GAP", "WARN") and score < 80]

    dimensions = [
        ComplianceDimensionOut(key=k, label=l, weight_pct=w, score_pct=s, status=st, detail=d)
        for k, l, w, s, st, d in dims
    ]
    score_pct = round(weighted, 1)
    grade = _grade(score_pct)
    now = utcnow()

    snapshot_id = None
    if persist:
        snap = PrivacyComplianceSnapshot(
            id=new_id(),
            regulation_code=code,
            score_pct=score_pct,
            grade=grade,
            gaps_json=json.dumps(gaps),
            dimensions_json=json.dumps([d.model_dump() for d in dimensions]),
            computed_at=now,
        )
        db.add(snap)
        db.commit()
        snapshot_id = snap.id

    return ComplianceScoreOut(
        regulation_code=code,
        regulation_name=reg.name,
        score_pct=score_pct,
        grade=grade,
        gaps=gaps,
        dimensions=dimensions,
        snapshot_id=snapshot_id,
        computed_at=now,
    )


def compare_regulations(db: Session, codes: list[str]) -> ComplianceCompareOut:
    normalized = [c.strip().upper() for c in codes if c.strip()]
    scores = [compute_compliance_score(db, c, persist=False) for c in normalized]
    matrix: dict[str, dict[str, float]] = {}
    if scores:
        all_keys = sorted({d.key for s in scores for d in s.dimensions})
        for key in all_keys:
            matrix[key] = {}
            for s in scores:
                for d in s.dimensions:
                    if d.key == key:
                        matrix[key][s.regulation_code] = d.score_pct
    return ComplianceCompareOut(codes=normalized, scores=scores, matrix=matrix)
