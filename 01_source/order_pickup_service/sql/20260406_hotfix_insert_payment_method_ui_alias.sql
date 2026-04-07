INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    default_wallet_provider_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'pmuia_creditcard_alt',
    'CREDITCARD',
    'creditCard',
    'chip',
    NULL,
    false,
    false,
    true,
    now(),
    now()
);


INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    default_wallet_provider_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'pmuia_debitcard_alt',
    'DEBITCARD',
    'debitCard',
    'chip',
    NULL,
    false,
    false,
    true,
    now(),
    now()
);




INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    default_wallet_provider_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'pmuia_giftcard_alt',
    'GIFTCARD',
    'giftCard',
    'chip',
    NULL,
    false,
    false,
    true,
    now(),
    now()
);



INSERT INTO payment_method_ui_alias (
    id,
    ui_code,
    canonical_method_code,
    default_payment_interface_code,
    default_wallet_provider_code,
    requires_customer_phone,
    requires_wallet_provider,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'pmuia_cartao_presente',
    'CARTAO_PRESENTE',
    'giftCard',
    'chip',
    NULL,
    false,
    false,
    true,
    now(),
    now()
);


