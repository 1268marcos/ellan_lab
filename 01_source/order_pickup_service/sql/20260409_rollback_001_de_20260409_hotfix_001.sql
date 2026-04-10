-- =====================================================
-- ROLLBACK: Remover as alterações do hotfix
-- =====================================================

-- 1. Remover o índice
DROP INDEX IF EXISTS public.idx_fiscal_order_attempt;

-- 2. Remover as funções criadas
DROP FUNCTION IF EXISTS get_latest_fiscal_attempt(TEXT);
DROP FUNCTION IF EXISTS get_active_fiscal_document(TEXT);

-- 3. Remover a view
DROP VIEW IF EXISTS public.vw_fiscal_documents_with_attempt;

-- 4. Remover as colunas adicionadas
ALTER TABLE public.fiscal_documents DROP COLUMN IF EXISTS attempt;
ALTER TABLE public.fiscal_documents DROP COLUMN IF EXISTS previous_receipt_code;
ALTER TABLE public.fiscal_documents DROP COLUMN IF EXISTS regenerated_at;
ALTER TABLE public.fiscal_documents DROP COLUMN IF EXISTS regenerate_reason;

-- 5. Recriar a constraint UNIQUE no order_id (se necessário)
-- Nota: Isso só funcionará se não houver duplicatas
-- ALTER TABLE public.fiscal_documents ADD CONSTRAINT fiscal_documents_order_id_key UNIQUE (order_id);