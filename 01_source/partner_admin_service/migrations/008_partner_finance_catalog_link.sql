-- Ligação canónica FINANCE ↔ Partners ↔ ML Admin

ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS finance_catalog_code character varying(48);
CREATE INDEX IF NOT EXISTS ix_partner_eco_finance_code ON partner_ecosystem_players (finance_catalog_code);
