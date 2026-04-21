BEGIN;

-- =========================================================
-- ELLAN LAB
-- 21/04/2026
-- Credits: validade de 30 dias + trilha temporal
-- =========================================================

-- 1) colunas novas
ALTER TABLE public.credits
    ADD COLUMN IF NOT EXISTS created_at timestamp with time zone,
    ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone,
    ADD COLUMN IF NOT EXISTS expires_at timestamp with time zone,
    ADD COLUMN IF NOT EXISTS used_at timestamp with time zone,
    ADD COLUMN IF NOT EXISTS revoked_at timestamp with time zone,
    ADD COLUMN IF NOT EXISTS source_type character varying(50),
    ADD COLUMN IF NOT EXISTS source_reason character varying(255),
    ADD COLUMN IF NOT EXISTS notes text;

-- 2) backfill determinístico
UPDATE public.credits
SET created_at = COALESCE(created_at, now())
WHERE created_at IS NULL;

UPDATE public.credits
SET updated_at = COALESCE(updated_at, created_at, now())
WHERE updated_at IS NULL;

UPDATE public.credits
SET expires_at = COALESCE(expires_at, created_at + interval '30 days')
WHERE expires_at IS NULL;

-- 3) tornar obrigatórias as colunas essenciais
ALTER TABLE public.credits
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL,
    ALTER COLUMN expires_at SET NOT NULL;

-- 4) defaults para novos registros
ALTER TABLE public.credits
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN updated_at SET DEFAULT now();

-- 5) checks de integridade
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_credits_amount_positive'
    ) THEN
        ALTER TABLE public.credits
            ADD CONSTRAINT ck_credits_amount_positive
            CHECK (amount_cents > 0);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_credits_expiry_after_create'
    ) THEN
        ALTER TABLE public.credits
            ADD CONSTRAINT ck_credits_expiry_after_create
            CHECK (expires_at > created_at);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_credits_used_after_create'
    ) THEN
        ALTER TABLE public.credits
            ADD CONSTRAINT ck_credits_used_after_create
            CHECK (used_at IS NULL OR used_at >= created_at);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_credits_revoked_after_create'
    ) THEN
        ALTER TABLE public.credits
            ADD CONSTRAINT ck_credits_revoked_after_create
            CHECK (revoked_at IS NULL OR revoked_at >= created_at);
    END IF;
END
$$;

-- 6) índices operacionais
CREATE INDEX IF NOT EXISTS ix_credits_user_id
    ON public.credits (user_id);

CREATE INDEX IF NOT EXISTS ix_credits_status
    ON public.credits (status);

CREATE INDEX IF NOT EXISTS ix_credits_expires_at
    ON public.credits (expires_at);

CREATE INDEX IF NOT EXISTS ix_credits_user_status_expires
    ON public.credits (user_id, status, expires_at);

COMMIT;