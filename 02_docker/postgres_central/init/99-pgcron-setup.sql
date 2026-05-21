-- Habilita pg_cron e agenda job mensal
DO $$
BEGIN
    -- Cria extensão se não existir
    CREATE EXTENSION IF NOT EXISTS pg_cron;
    
    -- Remove job antigo se existir (evita duplicação)
    PERFORM cron.unschedule('sync_locker_costs_monthly');
    
    -- Agenda novo job
    PERFORM cron.schedule(
        'sync_locker_costs_monthly',
        '0 2 2 * *',  -- Todo dia 2 às 02:00 UTC
        $$CALL sp_sync_locker_monthly_costs((date_trunc('month', now() - interval '1 month'))::date)$$
    );
    
    RAISE NOTICE 'pg_cron extension enabled and job scheduled successfully';
END $$;