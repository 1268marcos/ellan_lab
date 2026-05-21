from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.partner import EcommercePartner, LogisticsPartner
from app.models.user import User, UserRole
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {"users": 0, "user_roles": 0, "ecommerce": 0, "logistics": 0}
    now = _utcnow()

    users_seed = [
        ("usr-admin-ops", "Admin Operacao", "admin.operacao@ellanlab.com"),
        ("usr-suporte", "Suporte Ellan", "suporte@ellanlab.com"),
        ("usr-auditoria", "Auditoria Ellan", "auditoria@ellanlab.com"),
    ]
    for uid, name, email in users_seed:
        if not db.get(User, uid):
            db.add(
                User(
                    id=uid,
                    full_name=name,
                    email=email,
                    password_hash="!",
                    is_active=True,
                    email_verified=True,
                    phone_verified=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["users"] += 1

    roles_seed = [
        ("usr-admin-ops", "admin_operacao", "GLOBAL", None),
        ("usr-suporte", "suporte", "GLOBAL", None),
        ("usr-auditoria", "auditoria", "GLOBAL", None),
    ]
    for user_id, role, scope_type, scope_id in roles_seed:
        exists = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role == role,
                UserRole.scope_type == scope_type,
                UserRole.revoked_at.is_(None),
            )
            .first()
        )
        if not exists:
            db.add(
                UserRole(
                    id=new_id(),
                    user_id=user_id,
                    role=role,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    is_active=True,
                    granted_at=now,
                )
            )
            counts["user_roles"] += 1

    if not db.query(EcommercePartner).filter(EcommercePartner.code == "DEMO-EC").first():
        db.add(
            EcommercePartner(
                id="ec-demo-001",
                name="Demo E-commerce",
                code="DEMO-EC",
                integration_type="REST",
                api_base_url="https://api.demo-partner.example/v1",
                sla_pickup_hours=72,
                active=True,
                country="BR",
                status="ACTIVE",
                tier="STANDARD",
                support_email="ops@demo.example",
                created_at=now,
                updated_at=now,
            )
        )
        counts["ecommerce"] += 1

    if not db.query(LogisticsPartner).filter(LogisticsPartner.code == "DEMO-LG").first():
        db.add(
            LogisticsPartner(
                id="lg-demo-001",
                name="Demo Logistica",
                code="DEMO-LG",
                integration_type="REST",
                api_base_url="https://logistics.demo.example",
                tracking_url_template="https://track.demo.example/{code}",
                default_sla_hours=48,
                active=True,
                country="BR",
                created_at=now,
                updated_at=now,
            )
        )
        counts["logistics"] += 1

    db.commit()
    return counts
