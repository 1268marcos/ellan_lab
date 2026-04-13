-- ==========================================================
-- 3. Auditoria, Soft-Delete e Controle de Acesso (Versão Segura)
-- criação da tabela user_roles e audit_logs
-- ==========================================================

-- 3.1. Ajuste nas tabelas críticas
-- Usando IF NOT EXISTS nas colunas para evitar erros caso o script rode duas vezes
ALTER TABLE public.orders 
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS updated_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE public.lockers 
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS updated_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE public.users 
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS updated_by VARCHAR(36), 
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- 3.2. Índices de Performance para Soft-Delete
-- Usando IF NOT EXISTS para evitar o erro "already exists"
CREATE INDEX IF NOT EXISTS ix_orders_active ON public.orders(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_lockers_active ON public.lockers(deleted_at) WHERE deleted_at IS NULL;

-- 3.3. Perfis de acesso (RBAC)
CREATE TABLE IF NOT EXISTS public.user_roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id),
    role VARCHAR(40) NOT NULL, 
    scope_type VARCHAR(40) DEFAULT 'GLOBAL', 
    scope_id VARCHAR(36),
    is_active BOOLEAN DEFAULT true NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_role_active ON public.user_roles(user_id, role, scope_type, scope_id) WHERE revoked_at IS NULL;

-- 3.4. Log de auditoria de ações
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    actor_id VARCHAR(36) REFERENCES public.users(id),
    actor_role VARCHAR(40),
    action VARCHAR(80) NOT NULL,
    target_type VARCHAR(40) NOT NULL,
    target_id VARCHAR(36) NOT NULL,
    old_state JSONB,
    new_state JSONB,
    ip_address INET,
    user_agent TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- 3.5. Performance e Pesquisa em Auditoria
CREATE INDEX IF NOT EXISTS ix_audit_target ON public.audit_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS ix_audit_actor_time ON public.audit_logs(actor_id, occurred_at DESC);

-- Índices GIN para busca dentro do JSONB
CREATE INDEX IF NOT EXISTS ix_audit_logs_new_state_gin ON public.audit_logs USING GIN (new_state);
CREATE INDEX IF NOT EXISTS ix_audit_logs_old_state_gin ON public.audit_logs USING GIN (old_state);