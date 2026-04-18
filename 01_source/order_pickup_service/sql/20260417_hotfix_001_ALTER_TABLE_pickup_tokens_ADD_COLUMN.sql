-- 01_source/order_pickup_service/sql/20260417_add_manual_code_encrypted_to_pickup_tokens.sql
-- 17/04/2026 - suporte a manual_code criptografado com fallback legado

BEGIN;

ALTER TABLE public.pickup_tokens
    ADD COLUMN IF NOT EXISTS manual_code VARCHAR;

ALTER TABLE public.pickup_tokens
    ADD COLUMN IF NOT EXISTS manual_code_encrypted VARCHAR;

COMMIT;