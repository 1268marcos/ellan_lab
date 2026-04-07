BEGIN;

CREATE TABLE IF NOT EXISTS payment_method_ui_alias (
    id TEXT PRIMARY KEY,
    ui_code TEXT NOT NULL UNIQUE,
    canonical_method_code TEXT NOT NULL,
    default_payment_interface_code TEXT NULL,
    default_wallet_provider_code TEXT NULL,
    requires_customer_phone BOOLEAN NOT NULL DEFAULT FALSE,
    requires_wallet_provider BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_method_ui_alias_ui_code
    ON payment_method_ui_alias (ui_code);

CREATE INDEX IF NOT EXISTS idx_payment_method_ui_alias_canonical_method_code
    ON payment_method_ui_alias (canonical_method_code);

INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    default_wallet_provider_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active
) VALUES
    ('pmuia_pix', 'PIX', 'pix', 'qr_code', NULL, FALSE, FALSE, TRUE),
    ('pmuia_cartao_credito', 'CARTAO_CREDITO', 'creditCard', 'chip', NULL, FALSE, FALSE, TRUE),
    ('pmuia_cartao_debito', 'CARTAO_DEBITO', 'debitCard', 'chip', NULL, FALSE, FALSE, TRUE),
    ('pmuia_cartao_presente', 'CARTAO_PRESENTE', 'giftCard', 'manual', NULL, FALSE, FALSE, TRUE),
    ('pmuia_cartao_pre_pago', 'CARTAO_PRE_PAGO', 'prepaidCard', 'manual', NULL, FALSE, FALSE, TRUE),
    ('pmuia_mbway', 'MBWAY', 'mbway', 'phone_app', NULL, TRUE, FALSE, TRUE),
    ('pmuia_multibanco_reference', 'MULTIBANCO_REFERENCE', 'multibanco_reference', 'reference', NULL, FALSE, FALSE, TRUE),
    ('pmuia_nfc', 'NFC', 'nfc', 'nfc', NULL, FALSE, FALSE, TRUE),
    ('pmuia_apple_pay', 'APPLE_PAY', 'apple_pay', 'nfc', 'applePay', FALSE, TRUE, TRUE),
    ('pmuia_google_pay', 'GOOGLE_PAY', 'google_pay', 'nfc', 'googlePay', FALSE, TRUE, TRUE),
    ('pmuia_samsung_pay', 'SAMSUNG_PAY', 'samsung_pay', 'nfc', 'samsungPay', FALSE, TRUE, TRUE),
    ('pmuia_mercado_pago_wallet', 'MERCADO_PAGO_WALLET', 'mercado_pago_wallet', 'qr_code', 'mercadoPago', FALSE, TRUE, TRUE),
    ('pmuia_paypal', 'PAYPAL', 'paypal', 'web_redirect', 'paypal', FALSE, TRUE, TRUE),
    ('pmuia_m_pesa', 'M_PESA', 'm_pesa', 'ussd', 'mPesa', TRUE, TRUE, TRUE),
    ('pmuia_airtel_money', 'AIRTEL_MONEY', 'airtel_money', 'ussd', 'airtelMoney', TRUE, TRUE, TRUE),
    ('pmuia_mtn_money', 'MTN_MONEY', 'mtn_money', 'ussd', 'mtnMoney', TRUE, TRUE, TRUE),
    ('pmuia_alipay', 'ALIPAY', 'alipay', 'qr_code', 'alipay', FALSE, TRUE, TRUE),
    ('pmuia_wechat_pay', 'WECHAT_PAY', 'wechat_pay', 'qr_code', 'wechatPay', FALSE, TRUE, TRUE),
    ('pmuia_paypay', 'PAYPAY', 'paypay', 'qr_code', 'paypay', FALSE, TRUE, TRUE),
    ('pmuia_line_pay', 'LINE_PAY', 'line_pay', 'qr_code', 'linePay', FALSE, TRUE, TRUE),
    ('pmuia_rakuten_pay', 'RAKUTEN_PAY', 'rakuten_pay', 'qr_code', 'rakutenPay', FALSE, TRUE, TRUE),
    ('pmuia_konbini', 'KONBINI', 'konbini', 'barcode', NULL, FALSE, FALSE, TRUE),
    ('pmuia_go_pay', 'GO_PAY', 'go_pay', 'qr_code', 'goPay', TRUE, TRUE, TRUE),
    ('pmuia_ovo', 'OVO', 'ovo', 'qr_code', 'ovo', TRUE, TRUE, TRUE),
    ('pmuia_dana', 'DANA', 'dana', 'qr_code', 'dana', TRUE, TRUE, TRUE),
    ('pmuia_grabpay', 'GRABPAY', 'grabpay', 'qr_code', 'grabpay', FALSE, TRUE, TRUE),
    ('pmuia_gcash', 'GCASH', 'gcash', 'qr_code', 'gcash', TRUE, TRUE, TRUE),
    ('pmuia_paymaya', 'PAYMAYA', 'paymaya', 'qr_code', 'paymaya', TRUE, TRUE, TRUE),
    ('pmuia_tabby', 'TABBY', 'tabby', 'web_redirect', 'tabby', FALSE, TRUE, TRUE),
    ('pmuia_yoomoney', 'YOOMONEY', 'yoomoney', 'web_redirect', 'yoomoney', FALSE, TRUE, TRUE),
    ('pmuia_afterpay', 'AFTERPAY', 'afterpay', 'web_redirect', NULL, FALSE, FALSE, TRUE),
    ('pmuia_zip', 'ZIP', 'zip', 'web_redirect', NULL, FALSE, FALSE, TRUE),
    ('pmuia_bpay', 'BPAY', 'bpay', 'reference', NULL, FALSE, FALSE, TRUE),
    ('pmuia_boleto', 'BOLETO', 'boleto', 'barcode', NULL, FALSE, FALSE, TRUE),
    ('pmuia_crypto', 'CRYPTO', 'crypto', 'qr_code', NULL, FALSE, FALSE, TRUE)
ON CONFLICT (ui_code) DO UPDATE SET
    canonical_method_code = EXCLUDED.canonical_method_code,
    default_payment_interface_code = EXCLUDED.default_payment_interface_code,
    default_wallet_provider_code = EXCLUDED.default_wallet_provider_code,
    requires_customer_phone = EXCLUDED.requires_customer_phone,
    requires_wallet_provider = EXCLUDED.requires_wallet_provider,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;