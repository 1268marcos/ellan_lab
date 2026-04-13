-- SPRINT 2 - Escalabilidade & Dados Realistas
-- 1. Pricing Rules (Desacopla preço do produto)

CREATE TABLE public.pricing_rules (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    region VARCHAR(20),
    locker_id VARCHAR(36),
    product_category VARCHAR(64),
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE,
    base_amount_cents BIGINT NOT NULL,
    discount_pct DECIMAL(5,2) DEFAULT 0.00,
    min_amount_cents BIGINT,
    max_amount_cents BIGINT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
ALTER TABLE public.pricing_rules ADD CONSTRAINT ck_pricing_valid_range CHECK (valid_until IS NULL OR valid_until > valid_from);
CREATE INDEX ix_pricing_region_cat_active ON public.pricing_rules(region, product_category, is_active, valid_from) WHERE is_active = true;