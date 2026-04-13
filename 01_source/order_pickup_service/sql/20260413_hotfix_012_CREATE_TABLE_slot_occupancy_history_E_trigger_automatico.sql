-- 2. Slot Occupancy History + Trigger Automático
-- Rastreia cada mudança de estado do slot para análise de rotatividade, SLA e debugging.

CREATE TABLE public.slot_occupancy_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    locker_id VARCHAR NOT NULL,
    slot_label VARCHAR(20) NOT NULL,
    allocation_id VARCHAR(36),
    previous_state VARCHAR(40),
    current_state VARCHAR(40) NOT NULL,
    triggered_by VARCHAR(50), -- 'SYSTEM', 'USER', 'OPERATOR', 'TIMEOUT', 'SENSOR'
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX ix_slot_hist_locker_slot ON public.slot_occupancy_history(locker_id, slot_label, occurred_at DESC);
CREATE INDEX ix_slot_hist_allocation ON public.slot_occupancy_history(allocation_id);

-- Trigger automático: popula o histórico sempre que locker_slots muda
CREATE OR REPLACE FUNCTION trg_log_slot_state_change() RETURNS trigger AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO public.slot_occupancy_history (
            locker_id, slot_label, allocation_id, previous_state, current_state, triggered_by, metadata
        ) VALUES (
            NEW.locker_id, NEW.slot_label, NEW.current_allocation_id, OLD.status, NEW.status, 
            COALESCE(NEW.metadata->>'triggered_by', 'SYSTEM'), 
            jsonb_build_object('fault_code', NEW.fault_code, 'dimensions', jsonb_build_object('w', NEW.width_mm, 'h', NEW.height_mm, 'd', NEW.depth_mm))
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_slot_occupancy_history AFTER UPDATE ON public.locker_slots 
FOR EACH ROW EXECUTE FUNCTION trg_log_slot_state_change();

