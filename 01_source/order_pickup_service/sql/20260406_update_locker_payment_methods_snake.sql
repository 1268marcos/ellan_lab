UPDATE locker_payment_methods
SET method = CASE
    WHEN method = 'CARTAO_CREDITO' THEN 'creditCard'
    WHEN method = 'CARTAO_DEBITO' THEN 'debitCard'
    WHEN method = 'CARTAO_PRESENTE' THEN 'giftCard'
    WHEN method = 'PIX' THEN 'pix'
    WHEN method = 'MBWAY' THEN 'mbway'
    WHEN method = 'MULTIBANCO_REFERENCE' THEN 'multibanco_reference'
    WHEN method = 'APPLE_PAY' THEN 'apple_pay'
    WHEN method = 'GOOGLE_PAY' THEN 'google_pay'
    WHEN method = 'MERCADO_PAGO_WALLET' THEN 'mercado_pago_wallet'
    ELSE method
END,
updated_at = NOW()
WHERE method IN (
    'CARTAO_CREDITO',
    'CARTAO_DEBITO',
    'CARTAO_PRESENTE',
    'PIX',
    'MBWAY',
    'MULTIBANCO_REFERENCE',
    'APPLE_PAY',
    'GOOGLE_PAY',
    'MERCADO_PAGO_WALLET'
);