-- Readiness por blueprint de integração

ALTER TABLE finance_partner_readiness ADD COLUMN IF NOT EXISTS integration_blueprint_code character varying(40);
ALTER TABLE finance_partner_readiness ADD COLUMN IF NOT EXISTS blueprint_score integer DEFAULT 0 NOT NULL;
