BEGIN;

ALTER TABLE fiscal_documents
    ADD COLUMN IF NOT EXISTS cancel_reason TEXT,
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS chave_acesso VARCHAR(255),
    ADD COLUMN IF NOT EXISTS printed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS tax_amount_cents BIGINT,
    ADD COLUMN IF NOT EXISTS tax_breakdown_json JSONB,
    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS xml_signed BYTEA;

-- índices úteis
CREATE INDEX IF NOT EXISTS ix_fiscal_documents_tenant_id
    ON fiscal_documents (tenant_id);

CREATE INDEX IF NOT EXISTS ix_fiscal_documents_chave_acesso
    ON fiscal_documents (chave_acesso);

COMMIT;