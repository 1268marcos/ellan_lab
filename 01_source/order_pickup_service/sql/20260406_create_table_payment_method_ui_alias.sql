BEGIN;

CREATE TABLE IF NOT EXISTS payment_method_ui_alias (
    id TEXT PRIMARY KEY,
    ui_code TEXT NOT NULL UNIQUE,
    canonical_method_code TEXT NOT NULL,
    default_payment_interface_code TEXT,
    default_wallet_provider_code TEXT,
    requires_customer_phone BOOLEAN NOT NULL DEFAULT FALSE,
    requires_wallet_provider BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmui_ui_code
    ON payment_method_ui_alias (ui_code);

-- 🔥 DADOS MÍNIMOS PARA SEU CASO ATUAL

INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active
) VALUES
    (
        'pmuia_cartao_credito',
        'CARTAO_CREDITO',
        'creditCard',
        'chip',
        FALSE,
        FALSE,
        TRUE
    ),
    (
        'pmuia_cartao_debito',
        'CARTAO_DEBITO',
        'debitCard',
        'chip',
        FALSE,
        FALSE,
        TRUE
    ),
    (
        'pmuia_pix',
        'PIX',
        'pix',
        'qr_code',
        FALSE,
        FALSE,
        TRUE
    )
ON CONFLICT (ui_code) DO UPDATE
SET
    canonical_method_code = EXCLUDED.canonical_method_code,
    default_payment_interface_code = EXCLUDED.default_payment_interface_code,
    requires_customer_phone = EXCLUDED.requires_customer_phone,
    requires_wallet_provider = EXCLUDED.requires_wallet_provider,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;