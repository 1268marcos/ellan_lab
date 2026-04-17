-- =============================================================================
-- ELLAN LAB — Diagnóstico Completo de Pedido
-- Parâmetro: substitua o valor abaixo em :order_id
-- Retorna UMA linha com todas as informações agrupadas por domínio em JSON
-- 20260417_select_001_SELECT_informacoes_completas_pedido
-- =============================================================================

WITH
  _oid AS (
    SELECT '03323ec2-b606-44fd-a044-5ecd500cbb0f'::text AS id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 1. PEDIDO PRINCIPAL
  -- ─────────────────────────────────────────────────────────────────────────
  _order AS (
    SELECT o.*
    FROM public.orders o
    JOIN _oid ON o.id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 2. CLIENTE (usuário autenticado ou guest)
  -- ─────────────────────────────────────────────────────────────────────────
  _user AS (
    SELECT
      u.id              AS user_id,
      u.full_name            AS user_name,
      u.email           AS user_email,
      u.phone           AS user_phone,
      -- u.document        AS user_document,
      u.created_at      AS user_created_at
    FROM public.users u
    JOIN _order o ON u.id = o.user_id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 3. ITENS DO PEDIDO
  -- ─────────────────────────────────────────────────────────────────────────
  _items AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'sku_id',            oi.sku_id,
        'sku_description',   oi.sku_description,
        'quantity',          oi.quantity,
        'unit_amount_cents', oi.unit_amount_cents,
        'total_amount_cents',oi.total_amount_cents,
        'slot_size',         oi.slot_size,
        'item_status',       oi.item_status,
        'metadata',          oi.metadata_json
      ) ORDER BY oi.id
    ) AS data
    FROM public.order_items oi
    JOIN _oid ON oi.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 4. ALOCAÇÃO DE SLOT
  -- ─────────────────────────────────────────────────────────────────────────
  _alloc AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'allocation_id',   a.id,
        'locker_id',       a.locker_id,
        'slot',            a.slot,
        'slot_size',       a.slot_size,
        'state',           a.state,
        'locked_until',    a.locked_until,
        'allocated_at',    a.allocated_at,
        'released_at',     a.released_at,
        'release_reason',  a.release_reason,
        'ttl_seconds',     a.ttl_seconds,
        'created_at',      a.created_at,
        'updated_at',      a.updated_at
      ) ORDER BY a.created_at
    ) AS data
    FROM public.allocations a
    JOIN _oid ON a.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 5. LOCKER + SLOT FÍSICO (via alocação)
  -- ─────────────────────────────────────────────────────────────────────────
  _locker AS (
    SELECT jsonb_build_object(
      'locker_id',          l.id,
      'display_name',       l.display_name,
      'region',             l.region,
      'city',               l.city,
      'state',              l.state,
      'address_line',       l.address_line,
      'site_id',            l.site_id,
      'machine_id',         l.machine_id,
      'active',             l.active,
      'has_kiosk',          l.has_kiosk,
      'has_card_reader',    l.has_card_reader,
      'has_nfc',            l.has_nfc,
      'has_printer',        l.has_printer,
      'allowed_channels',   l.allowed_channels,
      'temperature_zone',   l.temperature_zone,
      'security_level',     l.security_level,
      'slots_count',        l.slots_count,
      'slots_available',    l.slots_available,
      'slot_fisico',        (
        SELECT jsonb_build_object(
          'slot_label',              ls.slot_label,
          'slot_size',               ls.slot_size,
          'status',                  ls.status,
          'occupied_since',          ls.occupied_since,
          'current_allocation_id',   ls.current_allocation_id,
          'last_opened_at',          ls.last_opened_at,
          'last_closed_at',          ls.last_closed_at,
          'fault_code',              ls.fault_code,
          'fault_detail',            ls.fault_detail
        )
        FROM public.locker_slots ls
        WHERE ls.locker_id = l.id
          AND ls.current_allocation_id = (
            SELECT a.id FROM public.allocations a
            JOIN _oid ON a.order_id = _oid.id
            WHERE a.locker_id = l.id
            ORDER BY a.created_at DESC
            LIMIT 1
          )
        LIMIT 1
      )
    ) AS data
    FROM public.lockers l
    WHERE l.id IN (
      SELECT DISTINCT a.locker_id
      FROM public.allocations a
      JOIN _oid ON a.order_id = _oid.id
      WHERE a.locker_id IS NOT NULL
    )
    LIMIT 1
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 6. HISTÓRICO DE OCUPAÇÃO DO SLOT
  -- ─────────────────────────────────────────────────────────────────────────
  _slot_history AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'locker_id',       soh.locker_id,
        'slot_label',      soh.slot_label,
        'previous_state',  soh.previous_state,
        'current_state',   soh.current_state,
        'triggered_by',    soh.triggered_by,
        -- 'changed_at',      soh.changed_at,
        'metadata',        soh.metadata
      ) ORDER BY soh.current_state -- soh.changed_at
    ) AS data
    FROM public.slot_occupancy_history soh
    WHERE soh.allocation_id IN (
      SELECT a.id FROM public.allocations a
      JOIN _oid ON a.order_id = _oid.id
    )
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 7. PICKUP (retirada pelo cliente)
  -- ─────────────────────────────────────────────────────────────────────────
  _pickup AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'pickup_id',        p.id,
        'channel',          p.channel,
        'region',           p.region,
        'locker_id',        p.locker_id,
        'machine_id',       p.machine_id,
        'slot',             p.slot,
        'status',           p.status,
        'lifecycle_stage',  p.lifecycle_stage,
        'current_token_id', p.current_token_id,
        'activated_at',     p.activated_at,
        'ready_at',         p.ready_at,
        'expires_at',       p.expires_at,
        'door_opened_at',   p.door_opened_at,
        'item_removed_at',  p.item_removed_at,
        'door_closed_at',   p.door_closed_at,
        'redeemed_at',      p.redeemed_at,
        'redeemed_via',     p.redeemed_via,
        'expired_at',       p.expired_at,
        'cancelled_at',     p.cancelled_at,
        'cancel_reason',    p.cancel_reason,
        'tokens',           (
          SELECT jsonb_agg(
            jsonb_build_object(
              'token_id',    pt.id,
              'expires_at',  pt.expires_at,
              'used_at',     pt.used_at,
              'is_active',   pt.is_active,
              'manual_code', pt.manual_code
            ) ORDER BY pt.created_at
          )
          FROM public.pickup_tokens pt
          WHERE pt.pickup_id = p.id
        )
      ) ORDER BY p.created_at
    ) AS data
    FROM public.pickups p
    JOIN _oid ON p.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 8. PAGAMENTO: Transações + Instruções + Splits
  -- ─────────────────────────────────────────────────────────────────────────
  _payment AS (
    SELECT jsonb_build_object(
      'transacoes', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'tx_id',                  pt.id,
            'gateway',                pt.gateway,
            'gateway_transaction_id', pt.gateway_transaction_id,
            'payment_method',         pt.payment_method,
            'amount_cents',           pt.amount_cents,
            'currency',               pt.currency,
            'status',                 pt.status,
            'card_brand',             pt.card_brand,
            'card_last4',             pt.card_last4,
            'card_type',              pt.card_type,
            'installments',           pt.installments,
            'nsu',                    pt.nsu,
            'authorization_code',     pt.authorization_code,
            'acquirer_name',          pt.acquirer_name,
            'initiated_at',           pt.initiated_at,
            'approved_at',            pt.approved_at,
            'settled_at',             pt.settled_at,
            'refunded_at',            pt.refunded_at,
            'refund_amount_cents',    pt.refund_amount_cents,
            'refund_reason',          pt.refund_reason,
            'error_code',             pt.error_code,
            'error_message',          pt.error_message,
            'reconciliation_status',  pt.reconciliation_status,
            'webhook_received_at',    pt.gateway_webhook_received_at
          ) ORDER BY pt.created_at
        )
        FROM public.payment_transactions pt
        JOIN _oid ON pt.order_id = _oid.id
      ),
      'instrucoes', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'instruction_id',   pi.id,
            'instruction_type', pi.instruction_type,
            'amount_cents',     pi.amount_cents,
            'status',           pi.status,
            'expires_at',       pi.expires_at,
            'qr_code_text',     pi.qr_code_text,
            'barcode',          pi.barcode,
            'authorization_code', pi.authorization_code,
            'wallet_provider',  pi.wallet_provider,
            'provider_name',    pi.provider_name,
            'captured_at',      pi.captured_at
          ) ORDER BY pi.created_at
        )
        FROM public.payment_instructions pi
        JOIN _oid ON pi.order_id = _oid.id
      ),
      'splits', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'recipient_type', ps.recipient_type,
            'recipient_id',   ps.recipient_id,
            'amount_cents',   ps.amount_cents,
            'percentage',     ps.percentage,
            'status',         ps.status,
            'settled_at',     ps.settled_at
          ) ORDER BY ps.created_at
        )
        FROM public.payment_splits ps
        JOIN _oid ON ps.order_id = _oid.id
      )
    ) AS data
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 9. FISCAL: Documentos Fiscais + Notas Fiscais (Invoices)
  -- ─────────────────────────────────────────────────────────────────────────
  _fiscal AS (
    SELECT jsonb_build_object(
      'documentos_fiscais', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'doc_id',               fd.id,
            'receipt_code',         fd.receipt_code,
            'document_type',        fd.document_type,
            'channel',              fd.channel,
            'region',               fd.region,
            'amount_cents',         fd.amount_cents,
            'currency',             fd.currency,
            'attempt',              fd.attempt,
            'send_status',          fd.send_status,
            'send_target',          fd.send_target,
            'print_status',         fd.print_status,
            'chave_acesso',         fd.chave_acesso,
            'issued_at',            fd.issued_at,
            'sent_at',              fd.sent_at,
            'printed_at',           fd.printed_at,
            'cancelled_at',         fd.cancelled_at,
            'cancel_reason',        fd.cancel_reason,
            'regenerated_at',       fd.regenerated_at,
            'regenerate_reason',    fd.regenerate_reason,
            'previous_receipt_code',fd.previous_receipt_code
          ) ORDER BY fd.attempt
        )
        FROM public.fiscal_documents fd
        JOIN _oid ON fd.order_id = _oid.id
      ),
      'notas_fiscais', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'invoice_id',        inv.id,
            'country',           inv.country,
            'invoice_type',      inv.invoice_type,
            'status',            inv.status,
            'invoice_number',    inv.invoice_number,
            'invoice_series',    inv.invoice_series,
            'access_key',        inv.access_key,
            'amount_cents',      inv.amount_cents,
            'issued_at',         inv.issued_at,
            'region',            inv.region,
            'retry_count',       inv.retry_count,
            'next_retry_at',     inv.next_retry_at,
            'last_error_code',   inv.last_error_code,
            'error_message',     inv.error_message,
            'dead_lettered_at',  inv.dead_lettered_at
          ) ORDER BY inv.created_at
        )
        FROM public.invoices inv
        JOIN _oid ON inv.order_id = _oid.id
      )
    ) AS data
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 10. CICLO DE VIDA: Prazos (PREPAYMENT_TIMEOUT / POSTPAYMENT_EXPIRY)
  -- ─────────────────────────────────────────────────────────────────────────
  _deadlines AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'deadline_key',    ld.deadline_key,
        'deadline_type',   ld.deadline_type,
        'order_channel',   ld.order_channel,
        'status',          ld.status,
        'due_at',          ld.due_at,
        'executed_at',     ld.executed_at,
        'cancelled_at',    ld.cancelled_at,
        'failure_count',   ld.failure_count
      ) ORDER BY ld.due_at
    ) AS data
    FROM public.lifecycle_deadlines ld
    JOIN _oid ON ld.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 11. NOTIFICAÇÕES ENVIADAS
  -- ─────────────────────────────────────────────────────────────────────────
  _notifications AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'template_key',          nl.template_key,
        'channel',               nl.channel,
        'destination_masked',    nl.destination_masked,
        'status',                nl.status,
        'attempt_count',         nl.attempt_count,
        'provider_name',         nl.provider_name,
        'sent_at',               nl.sent_at,
        'delivered_at',          nl.delivered_at,
        'failed_at',             nl.failed_at,
        'error_message',         nl.error_message,
        'locale',                nl.locale
      ) ORDER BY nl.created_at
    ) AS data
    FROM public.notification_logs nl
    JOIN _oid ON nl.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 12. FATURAMENTO: Eventos Processados de Billing
  -- ─────────────────────────────────────────────────────────────────────────
  _billing AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'event_key',     bpe.event_key,
        'status',        bpe.status,
        'error_message', bpe.error_message,
        'created_at',    bpe.created_at
      ) ORDER BY bpe.created_at
    ) AS data
    FROM public.billing_processed_events bpe
    JOIN _oid ON bpe.order_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 13. EVENTOS DE DOMÍNIO (aggregate_type = 'Order')
  -- ─────────────────────────────────────────────────────────────────────────
  _domain_events AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'event_key',      de.event_key,
        'event_name',     de.event_name,
        'event_version',  de.event_version,
        'status',         de.status,
        'occurred_at',    de.occurred_at,
        'published_at',   de.published_at,
        'payload',        de.payload
      ) ORDER BY de.occurred_at
    ) AS data
    FROM public.domain_events de
    JOIN _oid ON de.aggregate_id = _oid.id
    WHERE de.aggregate_type = 'Order'
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 14. OUTBOX DE EVENTOS (publicação assíncrona)
  -- ─────────────────────────────────────────────────────────────────────────
  _outbox AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'event_key',       deo.event_key,
        'event_name',      deo.event_name,
        'aggregate_type',  deo.aggregate_type,
        'status',          deo.status,
        'occurred_at',     deo.occurred_at,
        'published_at',    deo.published_at,
        'retry_count',     deo.retry_count,
        'next_retry_at',   deo.next_retry_at,
        'last_error',      deo.last_error
      ) ORDER BY deo.created_at
    ) AS data
    FROM public.domain_event_outbox deo
    JOIN _oid ON deo.aggregate_id = _oid.id
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 15. AUDITORIA (mudanças de estado no pedido)
  -- ─────────────────────────────────────────────────────────────────────────
  _audit AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'action',      al.action,
        'actor_id',    al.actor_id,
        'actor_role',  al.actor_role,
        'old_state',   al.old_state,
        'new_state',   al.new_state,
        'ip_address',  al.ip_address,
        'occurred_at', al.occurred_at
      ) ORDER BY al.occurred_at
    ) AS data
    FROM public.audit_logs al
    JOIN _oid ON al.target_id = _oid.id
    WHERE al.target_type = 'Order'
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 16. FINANCEIRO: Ledger + Créditos Gerados + Wallet Transactions
  -- ─────────────────────────────────────────────────────────────────────────
  _financeiro AS (
    SELECT jsonb_build_object(
      'ledger', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'entry_type',          fl.entry_type,
            'amount_cents',        fl.amount_cents,
            'currency',            fl.currency,
            'status',              fl.status,
            'external_reference',  fl.external_reference,
            'created_at',          fl.created_at,
            'metadata',            fl.metadata
          ) ORDER BY fl.created_at
        )
        FROM public.financial_ledger fl
        JOIN _oid ON fl.order_id = _oid.id
      ),
      'creditos', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'credit_id',    c.id,
            'user_id',      c.user_id,
            'amount_cents', c.amount_cents,
            'status',       c.status
          )
        )
        FROM public.credits c
        JOIN _oid ON c.order_id = _oid.id
      ),
      'wallet_transactions', (
        SELECT jsonb_agg(
          jsonb_build_object(
            'wallet_id',    wt.wallet_id,
            'type',         wt.type,
            'amount_cents', wt.amount_cents,
            -- 'currency',     wt.currency,
            'status',       wt.status,
            'description',  wt.description,
            'created_at',   wt.created_at
          ) ORDER BY wt.created_at
        )
        FROM public.wallet_transactions wt
        JOIN _oid ON wt.order_id = _oid.id
      )
    ) AS data
  ),

  -- ─────────────────────────────────────────────────────────────────────────
  -- 17. ANALYTICS FACTS
  -- ─────────────────────────────────────────────────────────────────────────
  _analytics AS (
    SELECT jsonb_agg(
      jsonb_build_object(
        'fact_key',       af.fact_key,
        'fact_name',      af.fact_name,
        'order_channel',  af.order_channel,
        'region_code',    af.region_code,
        'occurred_at',    af.occurred_at,
        'payload',        af.payload
      ) ORDER BY af.occurred_at
    ) AS data
    FROM public.analytics_facts af
    JOIN _oid ON af.order_id = _oid.id
  )

-- =============================================================================
-- SELECT FINAL: Uma linha, múltiplas colunas por domínio
-- =============================================================================
SELECT

  -- ── IDENTIFICAÇÃO RÁPIDA ──────────────────────────────────────────────────
  o.id                                    AS order_id,
  o.channel                               AS canal,
  o.status                                AS status_pedido,
  o.payment_status                        AS status_pagamento,
  o.payment_method                        AS metodo_pagamento,
  o.amount_cents                          AS valor_cents,
  o.currency                              AS moeda,
  o.region                                AS regiao,
  o.totem_id                              AS totem_id,
  o.site_id                               AS site_id,
  o.sku_id                                AS sku_id,
  o.sku_description                       AS sku_descricao,
  o.slot_size                             AS tamanho_slot,
  o.slot                                  AS slot_numero,
  o.paid_at                               AS pago_em,
  o.pickup_deadline_at                    AS prazo_retirada,
  o.picked_up_at                          AS retirado_em,
  o.cancelled_at                          AS cancelado_em,
  o.cancel_reason                         AS motivo_cancelamento,
  o.refunded_at                           AS reembolsado_em,
  o.refund_reason                         AS motivo_reembolso,
  o.created_at                            AS criado_em,
  o.updated_at                            AS atualizado_em,

  -- ── CLIENTE ───────────────────────────────────────────────────────────────
  jsonb_build_object(
    'user_id',       COALESCE(u.user_id,       o.user_id),
    'nome',          COALESCE(u.user_name,      o.guest_name),
    'email',         COALESCE(u.user_email,     o.guest_email,    o.receipt_email),
    'telefone',      COALESCE(u.user_phone,     o.guest_phone,    o.receipt_phone),
    -- 'documento',     u.user_document,
    'tipo',          CASE WHEN o.user_id IS NOT NULL THEN 'AUTENTICADO' ELSE 'GUEST' END,
    'session_id',    o.guest_session_id,
    'consent_marketing', o.consent_marketing,
    'consent_analytics', o.consent_analytics
  )                                       AS cliente,

  -- ── ITENS ─────────────────────────────────────────────────────────────────
  COALESCE(i.data, '[]')                  AS itens,

  -- ── ALOCAÇÃO ──────────────────────────────────────────────────────────────
  COALESCE(al.data, '[]')                 AS alocacoes,

  -- ── LOCKER FÍSICO ─────────────────────────────────────────────────────────
  COALESCE(lk.data, '{}')                 AS locker,

  -- ── HISTÓRICO DO SLOT ─────────────────────────────────────────────────────
  COALESCE(sh.data, '[]')                 AS historico_slot,

  -- ── PICKUP ────────────────────────────────────────────────────────────────
  COALESCE(pk.data, '[]')                 AS pickup,

  -- ── PAGAMENTO ─────────────────────────────────────────────────────────────
  py.data                                 AS pagamento,

  -- ── FISCAL ────────────────────────────────────────────────────────────────
  fs.data                                 AS fiscal,

  -- ── PRAZOS DO CICLO DE VIDA ───────────────────────────────────────────────
  COALESCE(dl.data, '[]')                 AS prazos_ciclo_vida,

  -- ── NOTIFICAÇÕES ──────────────────────────────────────────────────────────
  COALESCE(nt.data, '[]')                 AS notificacoes,

  -- ── FATURAMENTO ───────────────────────────────────────────────────────────
  COALESCE(bi.data, '[]')                 AS billing_events,

  -- ── EVENTOS DE DOMÍNIO ────────────────────────────────────────────────────
  COALESCE(de.data, '[]')                 AS domain_events,

  -- ── OUTBOX ────────────────────────────────────────────────────────────────
  COALESCE(ob.data, '[]')                 AS outbox_eventos,

  -- ── AUDITORIA ─────────────────────────────────────────────────────────────
  COALESCE(au.data, '[]')                 AS auditoria,

  -- ── FINANCEIRO (Ledger + Créditos + Wallet) ───────────────────────────────
  fn.data                                 AS financeiro,

  -- ── ANALYTICS ─────────────────────────────────────────────────────────────
  COALESCE(an.data, '[]')                 AS analytics_facts,

  -- ── RESUMO EXECUTIVO ──────────────────────────────────────────────────────
  jsonb_build_object(
    'order_id',          o.id,
    'canal',             o.channel,
    'status',            o.status,
    'pagamento_status',  o.payment_status,
    'valor_brl',         round(o.amount_cents::numeric / 100, 2),
    'metodo_pagamento',  o.payment_method,
    'sku',               o.sku_id,
    'slot_size',         o.slot_size,
    'locker',            (SELECT display_name FROM public.lockers WHERE id IN (SELECT locker_id FROM public.allocations WHERE order_id = o.id AND locker_id IS NOT NULL) LIMIT 1),
    'criado_em',         o.created_at,
    'pago_em',           o.paid_at,
    'prazo_retirada',    o.pickup_deadline_at,
    'retirado_em',       o.picked_up_at,
    'cancelado_em',      o.cancelled_at,
    'total_itens',       (SELECT COUNT(*) FROM public.order_items WHERE order_id = o.id),
    'total_notificacoes',(SELECT COUNT(*) FROM public.notification_logs WHERE order_id = o.id),
    'total_tentativas_nf',(SELECT COUNT(*) FROM public.fiscal_documents WHERE order_id = o.id),
    'tem_credito_gerado', (SELECT EXISTS(SELECT 1 FROM public.credits WHERE order_id = o.id)),
    'eventos_dominio',   (SELECT COUNT(*) FROM public.domain_events WHERE aggregate_id = o.id AND aggregate_type = 'Order'),
    'outbox_pendentes',  (SELECT COUNT(*) FROM public.domain_event_outbox WHERE aggregate_id = o.id AND status NOT IN ('PUBLISHED','FAILED'))
  )                                       AS resumo_executivo

FROM _order o
LEFT JOIN _user       u  ON TRUE
LEFT JOIN _items      i  ON TRUE
LEFT JOIN _alloc      al ON TRUE
LEFT JOIN _locker     lk ON TRUE
LEFT JOIN _slot_history sh ON TRUE
LEFT JOIN _pickup     pk ON TRUE
LEFT JOIN _payment    py ON TRUE
LEFT JOIN _fiscal     fs ON TRUE
LEFT JOIN _deadlines  dl ON TRUE
LEFT JOIN _notifications nt ON TRUE
LEFT JOIN _billing    bi ON TRUE
LEFT JOIN _domain_events de ON TRUE
LEFT JOIN _outbox     ob ON TRUE
LEFT JOIN _audit      au ON TRUE
LEFT JOIN _financeiro fn ON TRUE
LEFT JOIN _analytics  an ON TRUE;
