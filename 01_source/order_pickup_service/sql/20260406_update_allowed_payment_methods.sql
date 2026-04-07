UPDATE public.lockers
SET allowed_payment_methods =
    CASE
        WHEN region IN ('SP', 'RJ', 'PR', 'MG', 'RS', 'BA') THEN 'pix,boleto,creditCard,debitCard,cash,apple_pay,google_pay'
        WHEN region = 'PT' THEN 'mbway,multibanco_reference,creditCard,debitCard,cash,apple_pay,google_pay'
        WHEN region = 'JP' THEN 'konbini,creditCard,cash'
        WHEN region = 'KE' THEN 'm_pesa,cash'
        WHEN region IN ('US', 'US_NY', 'US_CA', 'US_TX', 'US_FL', 'US_IL') THEN 'creditCard,debitCard,apple_pay,google_pay,cash'
        WHEN region = 'CN' THEN 'alipay,wechat_pay,creditCard,apple_pay,google_pay'
        ELSE 'creditCard,debitCard,cash,pix'
    END
WHERE allowed_payment_methods = 'PIX,CARD,CASH';