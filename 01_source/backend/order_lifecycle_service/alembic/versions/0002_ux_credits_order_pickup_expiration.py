"""partial unique index: one PICKUP_EXPIRATION credit per order"""

from alembic import op


revision = "0002_ux_credits_order_pickup_expiration"
down_revision = "0001_init_order_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_credits_order_source
        ON public.credits (order_id, source_type)
        WHERE source_type = 'PICKUP_EXPIRATION'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.ux_credits_order_source")
