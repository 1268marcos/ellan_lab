"""init order lifecycle tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

"""
Migração para adicionar uma FOREIGN KEY de analytics_facts.order_id → orders.id,
com verificação prévia de registros órfãos e comentários sobre política ON DELETE.

ATENÇÃO: Execute a query de órfãos antes da migração para identificar dados inconsistentes!

Exemplo (substitua <schema> caso necessário):

    SELECT af.*
    FROM analytics_facts af
    LEFT JOIN orders o ON af.order_id = o.id
    WHERE o.id IS NULL;

Avalie o que fazer com registros órfãos (excluir/lidar manualmente) ANTES de criar a FK.

Opções de ON DELETE:
    - CASCADE: Ao deletar um order, apaga os analytics_facts relacionados. (+ automatiza limpeza, - cuidado: pode apagar dados úteis de analytics)
    - SET NULL: Ao deletar um order, order_id nos fatos vai para NULL. (+ preserva fato, - order_id deixa de ser obrigatório; pode afetar consultas)
    - RESTRICT/NO ACTION: Impede deletar se houver fatos. (+ evita perda, - pode travar exclusões legítimas)
Adapte conforme política de negócio. Aqui sugerimos CASCADE.
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # --- 1. (Opcional/documentação) Exemplo de consulta SQL para achar órfãos (execute manualmente antes/após):
    # SELECT af.* FROM analytics_facts af LEFT JOIN orders o ON af.order_id = o.id WHERE o.id IS NULL;

    # --- 2. (Recomenda-se corrigir órfãos caso exista, via script/manual; a migração pode falhar se houver!)
    # Exemplo de deleção de órfãos (execute manualmente após avaliação!):
    # DELETE FROM analytics_facts WHERE order_id NOT IN (SELECT id FROM orders);

    # --- 3. Criação da constraint com ON DELETE CASCADE:
    op.create_foreign_key(
        "fk_analytics_order",
        "analytics_facts",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE"
    )

    # --- 4. (Opcional): Validar constraint separadamente (Postgres padrão já valida):
    # op.execute("ALTER TABLE analytics_facts VALIDATE CONSTRAINT fk_analytics_order;")


def downgrade():
    op.drop_constraint("fk_analytics_order", "analytics_facts", type_="foreignkey")

revision = "0001_init_order_lifecycle"
down_revision = None
branch_labels = None
depends_on = None


deadline_type_enum = postgresql.ENUM(
    "PREPAYMENT_TIMEOUT",
    "POSTPAYMENT_EXPIRY",
    name="deadline_type_enum",
    create_type=False,
)

deadline_status_enum = postgresql.ENUM(
    "PENDING",
    "EXECUTING",
    "EXECUTED",
    "CANCELLED",
    "FAILED",
    name="deadline_status_enum",
    create_type=False,
)

event_status_enum = postgresql.ENUM(
    "PENDING",
    "PUBLISHED",
    "FAILED",
    name="event_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    deadline_type_enum.create(bind, checkfirst=True)
    deadline_status_enum.create(bind, checkfirst=True)
    event_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "lifecycle_deadlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("deadline_key", sa.String(length=200), nullable=False),
        sa.Column("order_id", sa.String(length=100), nullable=False),
        sa.Column("order_channel", sa.String(length=50), nullable=True),
        sa.Column("deadline_type", deadline_type_enum, nullable=False),
        sa.Column("status", deadline_status_enum, nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("deadline_key", name="uq_lifecycle_deadlines_deadline_key"),
    )
    op.create_index("ix_lifecycle_deadlines_due_at_status", "lifecycle_deadlines", ["due_at", "status"], unique=False)
    op.create_index("ix_lifecycle_deadlines_order_id", "lifecycle_deadlines", ["order_id"], unique=False)

    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_key", sa.String(length=200), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("event_name", sa.String(length=150), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", event_status_enum, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_key", name="uq_domain_events_event_key"),
    )
    op.create_index("ix_domain_events_aggregate_id", "domain_events", ["aggregate_id"], unique=False)

    op.create_table(
        "analytics_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("fact_key", sa.String(length=200), nullable=False),
        sa.Column("fact_name", sa.String(length=150), nullable=False),
        sa.Column("order_id", sa.String(length=100), nullable=False),
        sa.Column("order_channel", sa.String(length=50), nullable=True),
        sa.Column("region_code", sa.String(length=20), nullable=True),
        sa.Column("slot_id", sa.String(length=100), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fact_key", name="uq_analytics_facts_fact_key"),
    )
    op.create_index("ix_analytics_facts_fact_name_occurred_at", "analytics_facts", ["fact_name", "occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analytics_facts_fact_name_occurred_at", table_name="analytics_facts")
    op.drop_table("analytics_facts")

    op.drop_index("ix_domain_events_aggregate_id", table_name="domain_events")
    op.drop_table("domain_events")

    op.drop_index("ix_lifecycle_deadlines_order_id", table_name="lifecycle_deadlines")
    op.drop_index("ix_lifecycle_deadlines_due_at_status", table_name="lifecycle_deadlines")
    op.drop_table("lifecycle_deadlines")

    bind = op.get_bind()
    event_status_enum.drop(bind, checkfirst=True)
    deadline_status_enum.drop(bind, checkfirst=True)
    deadline_type_enum.drop(bind, checkfirst=True)