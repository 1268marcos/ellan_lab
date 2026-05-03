-- Materialização de scores LTV (BG/NBD + Gamma-Gamma) pelo ml_predictor_service.
-- Aplicar manualmente ou via pipeline de migração.

CREATE TABLE IF NOT EXISTS public.customer_ltv_scores (
    user_id character varying(36) PRIMARY KEY REFERENCES public.users (id) ON DELETE CASCADE,
    predicted_ltv_12m_cents bigint NOT NULL DEFAULT 0,
    ltv_p05_cents bigint NOT NULL DEFAULT 0,
    ltv_p95_cents bigint NOT NULL DEFAULT 0,
    churn_probability_30d numeric(12, 8) NOT NULL DEFAULT 0,
    p_alive numeric(12, 8),
    segmento_cliente character varying(32) NOT NULL,
    campaign_segment character varying(128) NOT NULL,
    features_90d jsonb NOT NULL DEFAULT '{}'::jsonb,
    notification_engagement_90d integer NOT NULL DEFAULT 0,
    consent_analytics boolean NOT NULL DEFAULT false,
    consent_marketing boolean NOT NULL DEFAULT false,
    model_version character varying(80) NOT NULL,
    scored_at timestamp with time zone NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS ix_customer_ltv_scores_segment ON public.customer_ltv_scores (segmento_cliente);
CREATE INDEX IF NOT EXISTS ix_customer_ltv_scores_scored_at ON public.customer_ltv_scores (scored_at DESC);
CREATE INDEX IF NOT EXISTS ix_customer_ltv_scores_campaign ON public.customer_ltv_scores (campaign_segment);

COMMENT ON TABLE public.customer_ltv_scores IS 'LTV 12m (centavos), churn 30d proxy e segmentação para campanhas; preenchido pelo ml_predictor_service.';
