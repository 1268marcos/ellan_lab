from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MlLockerNetworkPlayer(Base):
    """Rede/operador locker mundial (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT…)."""

    __tablename__ = "ml_locker_network_players"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(140), nullable=False)
    player_role = Column(String(40), nullable=False)
    parent_group = Column(String(32), nullable=False, default="LOCKER_NETWORK")
    country = Column(String(2), nullable=False)
    regions_json = Column(Text, nullable=False, default="[]")
    supports_lockers = Column(Boolean, nullable=False, default=True)
    supports_marketplace = Column(Boolean, nullable=False, default=False)
    integration_mode = Column(String(32), nullable=False, default="DIRECT_API")
    marketplace_channel_id = Column(String(36), nullable=True)
    marketplace_channel_code = Column(String(48), nullable=True, index=True)
    locker_operator_ref = Column(String(64), nullable=True)
    ecommerce_partner_code = Column(String(32), nullable=True)
    api_docs_url = Column(String(500), nullable=True)
    ml_scoring_weight = Column(Numeric(4, 2), nullable=False, default=1.0)
    ml_notes = Column(Text, nullable=True)
    global_tier = Column(String(16), nullable=False, default="REGIONAL")
    integration_status = Column(String(16), nullable=False, default="PLANNED")
    website_url = Column(String(500), nullable=True)
    parent_player_id = Column(String(36), ForeignKey("ml_locker_network_players.id", ondelete="SET NULL"), nullable=True)
    estimated_locker_count = Column(Integer, nullable=True)
    data_source = Column(String(32), nullable=False, default="CATALOG")
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MlNetworkMlProfile(Base):
    """Perfil ML por rede + caso de uso (telemetria, drift baseline, feature pack)."""

    __tablename__ = "ml_network_ml_profiles"
    __table_args__ = (UniqueConstraint("network_player_id", "use_case_id", name="uq_ml_network_profile"),)

    id = Column(String(36), primary_key=True)
    network_player_id = Column(
        String(36), ForeignKey("ml_locker_network_players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    use_case_id = Column(String(36), ForeignKey("ml_use_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    telemetry_density = Column(String(16), nullable=False, default="MEDIUM")
    drift_baseline_psi = Column(Numeric(6, 4), nullable=True, default=0.10)
    feature_pack_json = Column(Text, nullable=False, default="[]")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
