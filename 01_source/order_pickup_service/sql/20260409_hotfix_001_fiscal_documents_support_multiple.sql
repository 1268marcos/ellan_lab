-- =====================================================
-- HOTFIX: fiscal_documents - Suporte a múltiplas tentativas
-- Data: 09/04/2026
-- Descrição: Adiciona campos para rastrear reimpressões de documentos fiscais
-- =====================================================

-- 1. Adicionar novos campos
ALTER TABLE public.fiscal_documents 
ADD COLUMN IF NOT EXISTS attempt INTEGER DEFAULT 1 NOT NULL;

ALTER TABLE public.fiscal_documents 
ADD COLUMN IF NOT EXISTS previous_receipt_code VARCHAR(64);

ALTER TABLE public.fiscal_documents 
ADD COLUMN IF NOT EXISTS regenerated_at TIMESTAMP;

ALTER TABLE public.fiscal_documents 
ADD COLUMN IF NOT EXISTS regenerate_reason VARCHAR(255);

-- 2. Remover a constraint UNIQUE do order_id (se existir)
-- PostgreSQL: primeiro descobre o nome da constraint
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'public.fiscal_documents'::regclass
    AND conname LIKE '%order_id%'
    AND contype = 'u';
    
    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE public.fiscal_documents DROP CONSTRAINT %I', constraint_name);
        RAISE NOTICE 'Constraint % removida com sucesso', constraint_name;
    ELSE
        RAISE NOTICE 'Nenhuma constraint UNIQUE encontrada para order_id';
    END IF;
END;
$$;

-- 3. Criar novo índice composto para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_fiscal_order_attempt 
ON public.fiscal_documents (order_id, attempt);

-- 4. Atualizar registros existentes com attempt = 1 (primeira tentativa)
UPDATE public.fiscal_documents 
SET attempt = 1 
WHERE attempt IS NULL OR attempt = 0;

-- 5. (Opcional) Criar uma view para consultar documentos com número de tentativa
CREATE OR REPLACE VIEW public.vw_fiscal_documents_with_attempt AS
SELECT 
    id,
    order_id,
    receipt_code,
    document_type,
    channel,
    region,
    amount_cents,
    currency,
    delivery_mode,
    send_status,
    send_target,
    print_status,
    print_site_path,
    payload_json,
    issued_at,
    created_at,
    updated_at,
    attempt,
    previous_receipt_code,
    regenerated_at,
    regenerate_reason,
    CASE 
        WHEN attempt = 1 THEN 'PRIMEIRA_EMISSAO'
        ELSE 'REIMPRESSAO'
    END AS emission_type
FROM public.fiscal_documents;

-- 6. (Opcional) Criar função para obter a última tentativa de um pedido
CREATE OR REPLACE FUNCTION get_latest_fiscal_attempt(p_order_id TEXT)
RETURNS INTEGER AS $$
DECLARE
    latest_attempt INTEGER;
BEGIN
    SELECT COALESCE(MAX(attempt), 0) INTO latest_attempt
    FROM public.fiscal_documents
    WHERE order_id = p_order_id;
    
    RETURN latest_attempt;
END;
$$ LANGUAGE plpgsql;

-- 7. (Opcional) Criar função para obter o documento fiscal ativo de um pedido
CREATE OR REPLACE FUNCTION get_active_fiscal_document(p_order_id TEXT)
RETURNS TABLE (
    id TEXT,
    receipt_code TEXT,
    attempt INTEGER,
    issued_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fd.id,
        fd.receipt_code,
        fd.attempt,
        fd.issued_at
    FROM public.fiscal_documents fd
    WHERE fd.order_id = p_order_id
    ORDER BY fd.attempt DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 8. Verificar se as alterações foram aplicadas corretamente
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'fiscal_documents'
AND column_name IN ('attempt', 'previous_receipt_code', 'regenerated_at', 'regenerate_reason')
ORDER BY column_name;

-- 9. Mostrar estatísticas dos registros existentes
SELECT 
    COUNT(*) AS total_documents,
    COUNT(DISTINCT order_id) AS unique_orders,
    SUM(CASE WHEN attempt = 1 THEN 1 ELSE 0 END) AS first_attempts,
    SUM(CASE WHEN attempt > 1 THEN 1 ELSE 0 END) AS reprints
FROM public.fiscal_documents;