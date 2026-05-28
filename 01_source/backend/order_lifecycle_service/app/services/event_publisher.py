# 01_source/backend/order_lifecycle_service/app/services/event_publisher.py
import logging

from sqlalchemy.orm import Session

from app.models.lifecycle import DomainEvent, EventStatus
# -------------------------------------------------------------------
# 1. Exemplo de schema da tabela `outbox_events` (alembic, migrate em order_lifecycle)
"""
Exemplo para nova migration em alembic/versions/XXXX_add_outbox_events.py:

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'XXXX_add_outbox_events'
down_revision = '<ultima_migracao>'
def upgrade():
    op.create_table(
        'outbox_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('event_key', sa.String(length=200), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),  # PENDING | SENT | ACKED | FAILED
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer, default=0, nullable=False),
        sa.Column('last_error', sa.String(length=500), nullable=True),
        sa.UniqueConstraint('event_key', name='uq_outbox_event_key'),
        sa.Index('ix_outbox_events_status', 'status'),
        sa.Index('ix_outbox_events_created_at', 'created_at'),
    )
def downgrade():
    op.drop_table('outbox_events')
"""
# -------------------------------------------------------------------

# 2. Modelo SQLAlchemy OutboxEvent recomendado (em app/models/outbox_event.py)

# (Se for criar o modelo, ficaria algo assim:)
# from sqlalchemy import String, DateTime, Integer, JSON, UniqueConstraint, Index
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import Mapped, mapped_column
# import uuid
# from datetime import datetime
#
# from app.models.base import Base
#
# class OutboxEvent(Base):
#     __tablename__ = "outbox_events"
#     __table_args__ = (
#         UniqueConstraint("event_key", name="uq_outbox_event_key"),
#         Index("ix_outbox_events_status", "status"),
#         Index("ix_outbox_events_created_at", "created_at"),
#     )
#
#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     event_key: Mapped[str] = mapped_column(String(200), nullable=False)
#     payload: Mapped[dict] = mapped_column(JSON, nullable=False)
#     status: Mapped[str] = mapped_column(String(20), nullable=False)  # PENDING | SENT | ACKED | FAILED
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
#     sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
#     acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
#     retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
#     last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

# -------------------------------------------------------------------

# 3. Refatoração da função publish_pending_events para Outbox Pattern

from datetime import datetime, timezone
import uuid

from app.models.outbox_event import OutboxEvent  # Novo modelo

def publish_pending_events(db: Session) -> int:
    # Busca eventos do domínio ainda não processados pelo outbox
    # (No sistema real, você pode adicionar um filtro extra para evitar duplicidades)
    events = (
        db.query(DomainEvent)
        .filter(DomainEvent.status == EventStatus.PENDING)
        .order_by(DomainEvent.created_at.asc())
        .limit(100)
        .all()
    )

    now = datetime.now(timezone.utc)
    count = 0

    for event in events:
        # Constrói payload serializável (ajuste conforme o domínio)
        payload = {
            "event_name": event.event_name,
            "aggregate_id": event.aggregate_id,
            "event_key": event.event_key,
            "payload": event.payload,   # ou .data, conforme modelo DomainEvent
            "occurred_at": event.occurred_at.isoformat(),
        }
        # Evita duplicidade em caso de race (ideal: verificação de existência por event_key)
        already = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.event_key == event.event_key)
            .first()
        )
        if already:
            continue

        outbox_event = OutboxEvent(
            id=uuid.uuid4(),
            event_key=event.event_key,
            payload=payload,
            status="PENDING",
            created_at=now,
            retry_count=0,
        )
        db.add(outbox_event)

        # Marca evento de domínio como publicado (auditoria; outbox é quem garante publicação de fato)
        event.status = EventStatus.PUBLISHED
        event.published_at = now
        count += 1

    db.commit()
    return count

# -------------------------------------------------------------------

# 4. Estrutura base do worker assíncrono (event_outbox_worker.py)
#
# Este worker pode rodar em um processo separado, usando asyncio.

"""
Exemplo (simplificado, ajuste conforme cliente real Kafka/Rabbit):

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.outbox_event import OutboxEvent
from app.core.config import settings

logger = logging.getLogger("outbox_worker")
RETRY_BACKOFF = [5, 15, 60, 180, 600]  # segundos

async def publish_event(event: OutboxEvent) -> bool:
    # Envie o evento para o broker (Kafka, RabbitMQ). Exemplo fictício.
    try:
        # await kafka_producer.send("topic", value=event.payload)
        await asyncio.sleep(0.1)  # Simula envio
        return True
    except Exception as ex:
        logger.error("event_broker_publish_failed", extra={"event_key": event.event_key, "error": str(ex)})
        return False

async def process_pending_events(session_maker: async_sessionmaker):
    async with session_maker() as db:
        result = await db.execute(
            select(OutboxEvent).where(OutboxEvent.status == "PENDING").order_by(OutboxEvent.created_at.asc()).limit(50)
        )
        events = result.scalars().all()

        for event in events:
            ok = await publish_event(event)
            now = datetime.now(timezone.utc)
            if ok:
                event.status = "ACKED"
                event.acked_at = now
                event.sent_at = now
                event.last_error = None
                event.retry_count += 1
            else:
                event.status = "FAILED"
                event.last_error = "Publish failed"
                event.retry_count += 1
            await db.commit()

async def run_worker():
    engine = create_async_engine(settings.async_database_url, future=True)
    SessionMaker = async_sessionmaker(engine, expire_on_commit=False)
    while True:
        try:
            await process_pending_events(SessionMaker)
        except Exception as ex:
            logger.exception("outbox_worker_main_loop_failure")
        await asyncio.sleep(3)  # Ajuste intervalo conforme latência desejada

if __name__ == "__main__":
    asyncio.run(run_worker())
"""

# Alertas: monitore outbox_events PENDING e FAILED via Prometheus/grafana/health endpoint
#
# Exemplo de endpoint health:
# @router.get("/health/outbox")
# def outbox_health(db: Session = Depends(get_db)):
#     pending = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").count()
#     failed = db.query(OutboxEvent).filter(OutboxEvent.status == "FAILED").count()
#     return {"pending": pending, "failed": failed}

# -------------------------------------------------------------------

logger = logging.getLogger(__name__)


def publish_pending_events(db: Session) -> int:
    events = (
        db.query(DomainEvent)
        .filter(DomainEvent.status == EventStatus.PENDING)
        .order_by(DomainEvent.created_at.asc())
        .limit(100)
        .all()
    )

    count = 0
    for event in events:
        logger.info(
            "domain_event_recorded",
            extra={
                "event_name": event.event_name,
                "aggregate_id": event.aggregate_id,
                "event_key": event.event_key,
            },
        )
        event.status = EventStatus.PUBLISHED
        event.published_at = event.occurred_at
        count += 1

    return count