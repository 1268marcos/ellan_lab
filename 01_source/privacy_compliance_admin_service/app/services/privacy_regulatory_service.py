from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.privacy import PrivacyRegulation
from app.models.privacy_regulatory import (
    PrivacyLegitimateInterestAssessment,
    PrivacyOptOutRecord,
    PrivacyRegulatoryObligation,
    PrivacySubjectRight,
)
from app.schemas.privacy_regulatory import (
    AuthorityNoticeTemplateOut,
    LiaRecordCreate,
    OptOutRecordCreate,
    RegulatoryDomainSummaryOut,
    RegulatoryToolkitOut,
    RightsCompareOut,
    SubjectRightOut,
)
from app.services.crypto_util import new_id, utcnow
from app.services.privacy_webhook_emit import emit_privacy_webhook

AUTHORITY_TEMPLATES: dict[str, dict] = {
    "GDPR": {
        "authority_name": "Supervisory authority (lead DPA)",
        "deadline_hours": 72,
        "deadline_label": "72 hours from awareness (Art. 33)",
        "channel": "DPA portal / secure email",
        "template_summary": "Nature of breach, categories and approximate number of data subjects, DPO contact, likely consequences, measures taken.",
        "required_fields": ["breach_nature", "data_categories", "subjects_approx", "dpo_contact", "consequences", "measures"],
    },
    "UKGDPR": {
        "authority_name": "Information Commissioner's Office (ICO)",
        "deadline_hours": 72,
        "deadline_label": "72 hours (UK GDPR Art. 33)",
        "channel": "ICO breach reporting tool",
        "template_summary": "Same Art. 33 fields; include UK establishment and ICO registration reference.",
        "required_fields": ["breach_nature", "data_categories", "subjects_approx", "ico_ref", "measures"],
    },
    "LGPD": {
        "authority_name": "ANPD — Autoridade Nacional de Proteção de Dados",
        "deadline_hours": None,
        "deadline_label": "Prazo razoável — comunicação à ANPD e titulares (Art. 48)",
        "channel": "Canal ANPD / encarregado",
        "template_summary": "Descrição do incidente, dados afetados, medidas técnicas e de segurança, riscos aos titulares, ações de mitigação.",
        "required_fields": ["incident_description", "data_affected", "security_measures", "titular_risk", "mitigation"],
    },
    "CCPA": {
        "authority_name": "California Attorney General (CPRA)",
        "deadline_hours": None,
        "deadline_label": "Sem prazo fixo de 72h; notificação conforme CPRA e boas práticas",
        "channel": "AG portal / consumer notification",
        "template_summary": "Security breach notification to affected California residents; include opt-out impact if sale/share data involved.",
        "required_fields": ["breach_description", "data_types", "resident_notification", "remediation"],
    },
    "PIPEDA": {
        "authority_name": "Office of the Privacy Commissioner (OPC)",
        "deadline_hours": None,
        "deadline_label": "Real risk of significant harm — notify OPC and individuals",
        "channel": "OPC breach report form",
        "template_summary": "Circumstances, PI involved, remediation, harm assessment.",
        "required_fields": ["circumstances", "pi_involved", "harm_assessment", "remediation"],
    },
    "APPI": {
        "authority_name": "PPC Japan",
        "deadline_hours": None,
        "deadline_label": "Prompt report if required by APPI guidelines",
        "channel": "PPC notification",
        "template_summary": "Incident overview, personal data scope, countermeasures.",
        "required_fields": ["incident_overview", "data_scope", "countermeasures"],
    },
    "PDPA_SG": {
        "authority_name": "PDPC Singapore",
        "deadline_hours": 72,
        "deadline_label": "72 hours if significant harm (PDPA breach notification)",
        "channel": "PDPC e-notification",
        "template_summary": "Organisation details, breach facts, affected individuals, containment.",
        "required_fields": ["org_details", "breach_facts", "individuals_affected", "containment"],
    },
    "VCDPA": {
        "authority_name": "Virginia Attorney General",
        "deadline_hours": None,
        "deadline_label": "Notify AG if breach affects ≥1,000 VA residents",
        "channel": "AG consumer protection",
        "template_summary": "Nature of breach, categories of personal data, number of residents affected.",
        "required_fields": ["breach_nature", "data_categories", "residents_affected"],
    },
    "FADP": {
        "authority_name": "FDPIC (Switzerland)",
        "deadline_hours": None,
        "deadline_label": "Notify FDPIC if high risk to personality or legal rights",
        "channel": "FDPIC notification",
        "template_summary": "Controller identity, breach description, data categories, measures, DPO contact.",
        "required_fields": ["controller", "breach_description", "data_categories", "measures"],
    },
    "AU_PA": {
        "authority_name": "Office of the Australian Information Commissioner (OAIC)",
        "deadline_hours": 72,
        "deadline_label": "72 hours — eligible data breach (Notifiable Data Breaches scheme)",
        "channel": "OAIC NDB form",
        "template_summary": "Identity of entity, description of breach, kinds of information, recommendations for individuals.",
        "required_fields": ["entity_identity", "breach_description", "information_kinds", "recommendations"],
    },
}

BREACH_HOURS: dict[str, int | None] = {
    "GDPR": 72,
    "UKGDPR": 72,
    "LGPD": None,
    "CCPA": None,
    "PIPEDA": None,
    "APPI": None,
    "PDPA_SG": 72,
    "POPIA": None,
    "DPDP_IN": None,
    "VCDPA": None,
    "FADP": None,
    "AU_PA": 72,
}

SUPPORTED_REGULATIONS = [
    "GDPR",
    "UKGDPR",
    "LGPD",
    "CCPA",
    "VCDPA",
    "FADP",
    "PIPEDA",
    "APPI",
    "PDPA_SG",
    "POPIA",
    "DPDP_IN",
    "AU_PA",
]


def _authority_templates(code: str) -> list[AuthorityNoticeTemplateOut]:
    spec = AUTHORITY_TEMPLATES.get(code)
    if not spec:
        return []
    return [
        AuthorityNoticeTemplateOut(
            regulation_code=code,
            **spec,
        )
    ]


def list_subject_rights(db: Session, regulation_code: str | None = None) -> tuple[list[PrivacySubjectRight], int]:
    q = db.query(PrivacySubjectRight).filter(PrivacySubjectRight.active.is_(True))
    if regulation_code:
        q = q.filter(PrivacySubjectRight.regulation_code == regulation_code.upper())
    items = q.order_by(PrivacySubjectRight.regulation_code, PrivacySubjectRight.right_code).all()
    return items, len(items)


def list_obligations(
    db: Session,
    regulation_code: str | None = None,
    category: str | None = None,
    compliance_status: str | None = None,
) -> tuple[list[PrivacyRegulatoryObligation], int]:
    q = db.query(PrivacyRegulatoryObligation).filter(PrivacyRegulatoryObligation.active.is_(True))
    if regulation_code:
        q = q.filter(PrivacyRegulatoryObligation.regulation_code == regulation_code.upper())
    if category:
        q = q.filter(PrivacyRegulatoryObligation.category == category.upper())
    if compliance_status:
        q = q.filter(PrivacyRegulatoryObligation.compliance_status == compliance_status.upper())
    items = q.order_by(PrivacyRegulatoryObligation.regulation_code, PrivacyRegulatoryObligation.category).all()
    return items, len(items)


def update_obligation(db: Session, obligation_id: str, patch: dict) -> PrivacyRegulatoryObligation:
    row = db.get(PrivacyRegulatoryObligation, obligation_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="obligation_not_found")
    for key, val in patch.items():
        if val is not None:
            setattr(row, key, val)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_lia(db: Session, regulation_code: str | None = None) -> tuple[list[PrivacyLegitimateInterestAssessment], int]:
    q = db.query(PrivacyLegitimateInterestAssessment)
    if regulation_code:
        q = q.filter(PrivacyLegitimateInterestAssessment.regulation_code == regulation_code.upper())
    items = q.order_by(PrivacyLegitimateInterestAssessment.created_at.desc()).all()
    return items, len(items)


def create_lia(db: Session, payload: LiaRecordCreate) -> PrivacyLegitimateInterestAssessment:
    now = utcnow()
    row = PrivacyLegitimateInterestAssessment(
        id=new_id(),
        regulation_code=payload.regulation_code.upper(),
        processing_activity_id=payload.processing_activity_id,
        title=payload.title,
        purpose=payload.purpose,
        balancing_test_summary=payload.balancing_test_summary,
        status=payload.status,
        reviewer=payload.reviewer,
        reviewed_at=now if payload.status == "APPROVED" else None,
        document_url=payload.document_url,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_opt_outs(db: Session, regulation_code: str | None = None, active_only: bool = True) -> tuple[list[PrivacyOptOutRecord], int]:
    q = db.query(PrivacyOptOutRecord)
    if regulation_code:
        q = q.filter(PrivacyOptOutRecord.regulation_code == regulation_code.upper())
    if active_only:
        q = q.filter(PrivacyOptOutRecord.active.is_(True))
    items = q.order_by(PrivacyOptOutRecord.recorded_at.desc()).all()
    return items, len(items)


def create_opt_out(db: Session, payload: OptOutRecordCreate) -> PrivacyOptOutRecord:
    now = utcnow()
    row = PrivacyOptOutRecord(
        id=new_id(),
        regulation_code=payload.regulation_code.upper(),
        user_id=payload.user_id,
        guest_identifier=payload.guest_identifier,
        opt_out_type=payload.opt_out_type,
        signal_source=payload.signal_source,
        gpc_signal=payload.gpc_signal,
        active=True,
        recorded_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    emit_privacy_webhook(
        db,
        regulation_code=row.regulation_code,
        event_name="opt_out.recorded",
        payload={
            "opt_out_id": row.id,
            "opt_out_type": row.opt_out_type,
            "signal_source": row.signal_source,
            "gpc_signal": row.gpc_signal,
            "user_id": row.user_id,
            "guest_identifier": row.guest_identifier,
            "active": row.active,
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        },
        aggregate_id=row.id,
    )
    return row


_DSAR_DETAIL_TEMPLATES: dict[str, dict[str, str]] = {
    "ACCESS": {
        "en": "I request access to all personal data you hold about me related to locker pickup, orders, and account activity.",
        "pt": "Solicito acesso a todos os dados pessoais que tratam sobre mim relativos a retirada em locker, pedidos e conta.",
    },
    "DELETION": {
        "en": "I request erasure/deletion of my personal data, subject to legal retention exceptions.",
        "pt": "Solicito eliminação dos meus dados pessoais, ressalvadas obrigações legais de conservação.",
    },
    "RECTIFICATION": {
        "en": "I request correction of inaccurate personal data in my profile and pickup records.",
        "pt": "Solicito correção de dados pessoais inexatos no meu cadastro e histórico de retirada.",
    },
    "PORTABILITY": {
        "en": "I request a machine-readable export of my personal data (pickup history, consents, identifiers).",
        "pt": "Solicito portabilidade dos meus dados em formato estruturado (histórico de retirada, consentimentos).",
    },
    "RESTRICTION": {
        "en": "I request restriction of processing of my personal data pending review.",
        "pt": "Solicito limitação do tratamento dos meus dados pessoais até revisão do pedido.",
    },
    "OBJECTION": {
        "en": "I object to processing based on legitimate interest / opt-out of sale or targeted advertising.",
        "pt": "Oponho-me ao tratamento por interesse legítimo / opt-out de venda ou publicidade direcionada.",
    },
}


def build_dsar_draft(
    db: Session,
    *,
    regulation_code: str,
    right_code: str | None = None,
    right_id: str | None = None,
) -> dict:
    code = regulation_code.upper()
    reg = db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")

    right: PrivacySubjectRight | None = None
    if right_id:
        right = db.get(PrivacySubjectRight, right_id)
    elif right_code:
        right = (
            db.query(PrivacySubjectRight)
            .filter(
                PrivacySubjectRight.regulation_code == code,
                PrivacySubjectRight.right_code == right_code.upper(),
                PrivacySubjectRight.active.is_(True),
            )
            .first()
        )
    if not right:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject_right_not_found")

    dsar_type = (right.dsar_type or "ACCESS").upper()
    lang = "pt" if code in ("LGPD",) else "en"
    base_detail = _DSAR_DETAIL_TEMPLATES.get(dsar_type, _DSAR_DETAIL_TEMPLATES["ACCESS"]).get(lang)
    article = right.article_ref or "applicable law"
    details = (
        f"{base_detail}\n\n"
        f"Right exercised: {right.name} ({right.right_code}) under {code} — {article}. "
        f"ELLAN Lab locker platform. Please confirm receipt and expected response by SLA."
    )
    subject_line = f"[DSAR/{code}] {right.right_code} — {right.name}"

    return {
        "regulation_code": code,
        "regulation_name": reg.name,
        "request_type": dsar_type,
        "right_id": right.id,
        "right_code": right.right_code,
        "right_name": right.name,
        "article_ref": right.article_ref,
        "response_sla_days": right.response_sla_days or str(reg.response_sla_days),
        "automated_available": right.automated_available,
        "details": details,
        "subject_line": subject_line,
    }


def _obligations_compliant_pct(obligations: list[PrivacyRegulatoryObligation]) -> float:
    if not obligations:
        return 0.0
    compliant = sum(1 for o in obligations if o.compliance_status == "COMPLIANT")
    return round(compliant / len(obligations) * 100, 1)


def get_toolkit(db: Session, regulation_code: str) -> RegulatoryToolkitOut:
    code = regulation_code.upper()
    reg = db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")

    rights, _ = list_subject_rights(db, code)
    obligations, _ = list_obligations(db, code)
    lia, _ = list_lia(db, code)
    opt_outs, _ = list_opt_outs(db, code)

    summary = RegulatoryDomainSummaryOut(
        regulation_code=code,
        subject_rights_count=len(rights),
        obligations_count=len(obligations),
        obligations_compliant_pct=_obligations_compliant_pct(obligations),
        lia_count=len(lia),
        opt_out_count=len(opt_outs),
        breach_notification_hours=BREACH_HOURS.get(code),
    )

    return RegulatoryToolkitOut(
        regulation_code=code,
        regulation_name=reg.name,
        jurisdiction=reg.jurisdiction,
        summary=summary,
        subject_rights=[SubjectRightOut.model_validate(r) for r in rights],
        obligations=obligations,
        lia_records=lia,
        opt_out_records=opt_outs,
        authority_templates=_authority_templates(code),
        supported_regulations=SUPPORTED_REGULATIONS,
    )


def compare_rights(db: Session, codes: list[str]) -> RightsCompareOut:
    normalized = [c.strip().upper() for c in codes if c.strip()]
    rights_by_code: dict[str, list[SubjectRightOut]] = {}
    dsar_sets: dict[str, set[str]] = {}
    for code in normalized:
        items, _ = list_subject_rights(db, code)
        rights_by_code[code] = [SubjectRightOut.model_validate(r) for r in items]
        dsar_sets[code] = {r.right_code for r in items}

    common = set.intersection(*dsar_sets.values()) if dsar_sets else set()
    unique_by_code = {code: sorted(dsar_sets.get(code, set()) - common) for code in normalized}

    all_dsar = sorted({r.dsar_type for rights in rights_by_code.values() for r in rights if r.dsar_type})
    return RightsCompareOut(
        codes=normalized,
        rights_by_code=rights_by_code,
        common_dsar_types=all_dsar,
        unique_by_code=unique_by_code,
    )


def obligations_score_for_regulation(db: Session, regulation_code: str) -> tuple[float, str]:
    obligations, _ = list_obligations(db, regulation_code)
    if not obligations:
        return 50.0, "Sem obrigacoes catalogadas"
    pct = _obligations_compliant_pct(obligations)
    partial = sum(1 for o in obligations if o.compliance_status == "PARTIAL")
    pending = sum(1 for o in obligations if o.compliance_status in ("PENDING", "NON_COMPLIANT"))
    status = "OK" if pct >= 80 else ("WARN" if pct >= 50 else "GAP")
    detail = f"{len(obligations)} obrigacoes · {pct:.0f}% compliant · {partial} parciais · {pending} pendentes"
    return pct, detail if status != "OK" else f"{len(obligations)} obrigacoes regulatorias mapeadas"
