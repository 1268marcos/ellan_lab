# 01_source/backend/billing_fiscal_service/app/utils/id_generator.py
import uuid

def generate_invoice_id() -> str:
    return f"inv_{uuid.uuid4().hex}"