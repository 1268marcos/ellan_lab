# 01_source/backend/billing_fiscal_service/app/core/db_migrations.py
from sqlalchemy import inspect
from app.models.base import Base
from app.models.invoice_model import Invoice


def run_startup_migrations(engine):
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "invoices" not in tables:
        raise RuntimeError("Tabela invoices não foi criada corretamente")