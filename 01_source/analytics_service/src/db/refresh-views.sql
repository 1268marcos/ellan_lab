-- Refresh automático de materialized views via pg_cron
-- Executar: psql "$DATABASE_URL" -f src/db/refresh-views.sql

CREATE EXTENSION IF NOT EXISTS pg_cron;

CREATE TABLE IF NOT EXISTS public.mv_refresh_log (
    id              BIGSERIAL PRIMARY KEY,
    view_name       VARCHAR(120) NOT NULL,
    status          VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'ALERT')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    duration_ms     INTEGER,
    error_message   TEXT,
    triggered_by    VARCHAR(60) NOT NULL DEFAULT 'pg_cron',
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_mv_refresh_log_view_started
    ON public.mv_refresh_log (view_name, started_at DESC);

CREATE INDEX IF NOT EXISTS ix_mv_refresh_log_status_started
    ON public.mv_refresh_log (status, started_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_realtime_kpis_snapshot
    ON public.mv_realtime_kpis (snapshot_time);

CREATE OR REPLACE FUNCTION public.fn_log_mv_refresh_start(
    p_view_name VARCHAR,
    p_triggered_by VARCHAR DEFAULT 'pg_cron'
) RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    INSERT INTO public.mv_refresh_log (view_name, status, triggered_by)
    VALUES (p_view_name, 'SUCCESS', COALESCE(p_triggered_by, 'pg_cron'))
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_log_mv_refresh_finish(
    p_log_id BIGINT,
    p_status VARCHAR,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.mv_refresh_log
    SET status = p_status,
        finished_at = now(),
        duration_ms = EXTRACT(EPOCH FROM (now() - started_at)) * 1000,
        error_message = p_error_message
    WHERE id = p_log_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_refresh_mv_locker_monthly_profitability(
    p_triggered_by VARCHAR DEFAULT 'pg_cron'
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_log_id BIGINT;
    v_populated BOOLEAN;
BEGIN
    v_log_id := public.fn_log_mv_refresh_start('mv_locker_monthly_profitability', p_triggered_by);
    SELECT relispopulated INTO v_populated
    FROM pg_class
    WHERE oid = 'public.mv_locker_monthly_profitability'::regclass;
    BEGIN
        IF COALESCE(v_populated, false) THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_locker_monthly_profitability;
        ELSE
            REFRESH MATERIALIZED VIEW public.mv_locker_monthly_profitability;
        END IF;
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'SUCCESS');
    EXCEPTION WHEN OTHERS THEN
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'FAILED', SQLERRM);
        RAISE;
    END;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_refresh_mv_realtime_kpis(
    p_triggered_by VARCHAR DEFAULT 'pg_cron'
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_log_id BIGINT;
    v_populated BOOLEAN;
BEGIN
    v_log_id := public.fn_log_mv_refresh_start('mv_realtime_kpis', p_triggered_by);
    SELECT relispopulated INTO v_populated
    FROM pg_class
    WHERE oid = 'public.mv_realtime_kpis'::regclass;
    BEGIN
        IF COALESCE(v_populated, false) THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_realtime_kpis;
        ELSE
            REFRESH MATERIALIZED VIEW public.mv_realtime_kpis;
        END IF;
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'SUCCESS');
    EXCEPTION WHEN OTHERS THEN
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'FAILED', SQLERRM);
        RAISE;
    END;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_refresh_financial_dashboard(
    p_triggered_by VARCHAR DEFAULT 'pg_cron'
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_log_id BIGINT;
    v_populated BOOLEAN;
BEGIN
    v_log_id := public.fn_log_mv_refresh_start('v_financial_dashboard', p_triggered_by);
    SELECT relispopulated INTO v_populated
    FROM pg_class
    WHERE oid = 'public.mv_locker_monthly_profitability'::regclass;
    BEGIN
        IF COALESCE(v_populated, false) THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_locker_monthly_profitability;
        ELSE
            REFRESH MATERIALIZED VIEW public.mv_locker_monthly_profitability;
        END IF;
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'SUCCESS');
    EXCEPTION WHEN OTHERS THEN
        PERFORM public.fn_log_mv_refresh_finish(v_log_id, 'FAILED', SQLERRM);
        RAISE;
    END;
END;
$$;

DO $$
BEGIN
    PERFORM cron.unschedule('refresh_mv_locker_monthly_profitability');
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$
BEGIN
    PERFORM cron.unschedule('refresh_mv_realtime_kpis');
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$
BEGIN
    PERFORM cron.unschedule('refresh_v_financial_dashboard');
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

SELECT cron.schedule(
    'refresh_mv_locker_monthly_profitability',
    '0 * * * *',
    $$SELECT public.fn_refresh_mv_locker_monthly_profitability('pg_cron')$$
);

SELECT cron.schedule(
    'refresh_mv_realtime_kpis',
    '*/5 * * * *',
    $$SELECT public.fn_refresh_mv_realtime_kpis('pg_cron')$$
);

SELECT cron.schedule(
    'refresh_v_financial_dashboard',
    '0 * * * *',
    $$SELECT public.fn_refresh_financial_dashboard('pg_cron')$$
);

GRANT SELECT ON public.mv_refresh_log TO admin;
GRANT EXECUTE ON FUNCTION public.fn_refresh_mv_locker_monthly_profitability(VARCHAR) TO admin;
GRANT EXECUTE ON FUNCTION public.fn_refresh_mv_realtime_kpis(VARCHAR) TO admin;
GRANT EXECUTE ON FUNCTION public.fn_refresh_financial_dashboard(VARCHAR) TO admin;
