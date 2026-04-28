-- queries_grafana_metabase.sql
-- Exemplos de queries para dashboards (market-data ready).

-- =========================
-- Grafana (monitoramento técnico / trading)
-- =========================

-- Últimos 500 ticks de um ativo
-- variável esperada no painel: $symbol
SELECT time, price, volume, side
FROM market_ticks
WHERE symbol = $symbol
  AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC
LIMIT 500;

-- Volume por exchange nas últimas 24h
SELECT exchange, SUM(volume) AS total_vol
FROM market_ticks
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY exchange
ORDER BY total_vol DESC;

-- =========================
-- Metabase (BI / backtesting)
-- =========================

-- OHLCV diário dos últimos 30 dias (agregado sobre candle_1h)
-- parâmetro esperado no Metabase: {{symbol}}
SELECT
    time_bucket('1 day', bucket) AS day_bucket,
    symbol,
    FIRST(open, bucket) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, bucket) AS close,
    SUM(total_volume) AS total_volume
FROM candle_1h
WHERE bucket >= NOW() - INTERVAL '30 days'
  AND symbol = {{symbol}}
GROUP BY day_bucket, symbol
ORDER BY day_bucket;

-- ============================================================================
-- Expansão por perfil de equipe (Trading / Risco / Operações / Negócio)
-- ============================================================================

-- =========================
-- Trading / Quant
-- =========================

-- Candlestick OHLCV por intervalo
-- Grafana vars esperadas: $symbol, $interval (ex.: '5 min', '1 hour')
SELECT
  time_bucket($interval, time) AS ts,
  symbol,
  FIRST(price, time) AS open,
  MAX(price) AS high,
  MIN(price) AS low,
  LAST(price, time) AS close,
  SUM(volume) AS vol
FROM market_ticks
WHERE symbol = $symbol
  AND time BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY ts, symbol
ORDER BY ts;

-- Spread (quando houver bid/ask em tabela compatível)
-- Ajustar para sua tabela de book/ticks enriquecidos.
-- SELECT time, (ask_price - bid_price) AS spread
-- FROM market_ticks
-- WHERE symbol = $symbol
--   AND time >= NOW() - INTERVAL '10 min'
-- ORDER BY time;

-- =========================
-- Risco / Compliance
-- =========================

-- Exposição por ativo (exemplo genérico, requer tabela positions)
-- SELECT p.symbol, SUM(p.position_size * t.price) AS exposure
-- FROM positions p
-- JOIN LATERAL (
--   SELECT price
--   FROM market_ticks mt
--   WHERE mt.symbol = p.symbol
--   ORDER BY mt.time DESC
--   LIMIT 1
-- ) t ON TRUE
-- GROUP BY p.symbol
-- ORDER BY exposure DESC;

-- VaR histórico rolling simplificado (retornos por ativo)
WITH returns AS (
  SELECT
    time_bucket('1 day', time) AS day_ref,
    symbol,
    (price - LAG(price) OVER (PARTITION BY symbol ORDER BY time))
      / NULLIF(LAG(price) OVER (PARTITION BY symbol ORDER BY time), 0) AS daily_return
  FROM market_ticks
)
SELECT
  day_ref,
  percentile_cont(0.05) WITHIN GROUP (ORDER BY daily_return) AS var_95
FROM returns
WHERE daily_return IS NOT NULL
GROUP BY day_ref
ORDER BY day_ref;

-- =========================
-- Operações / DevOps
-- =========================

-- Throughput de ingestão (linhas/min)
SELECT time_bucket('1 min', time) AS ts, COUNT(*) AS rows_per_min
FROM market_ticks
GROUP BY ts
ORDER BY ts DESC
LIMIT 60;

-- Uso de storage por chunk (Timescale)
SELECT
  chunk_name,
  compressed,
  uncompressed_total_bytes,
  compressed_total_bytes
FROM timescaledb_information.chunks
WHERE hypertable_name = 'market_ticks'
ORDER BY range_start DESC;

-- =========================
-- Negócio / Produto
-- =========================

-- Receita por estratégia (exemplo, requer tabela trades)
-- SELECT strategy, DATE(exec_time) AS day_ref, SUM(fee) AS revenue
-- FROM trades
-- WHERE exec_time >= NOW() - INTERVAL '30 days'
-- GROUP BY strategy, day_ref
-- ORDER BY day_ref;

-- ============================================================================
-- FA-5 Financeiro (inadimplência + reconciliação)
-- ============================================================================

-- 1) Inadimplência operacional diária (KPI)
SELECT
  snapshot_date,
  partner_id,
  COALESCE(locker_id, 'GLOBAL') AS locker_id,
  ar_open_cents,
  dso_days,
  active_invoice_count
FROM financial_kpi_daily
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY snapshot_date DESC, dso_days DESC;

-- 2) Tendência de DSO (média diária)
SELECT
  snapshot_date,
  AVG(dso_days) AS avg_dso_days
FROM financial_kpi_daily
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '60 days'
GROUP BY snapshot_date
ORDER BY snapshot_date;

-- 3) Receita reconhecida diária (soma)
SELECT
  recognition_date,
  SUM(recognized_amount_cents) AS recognized_amount_cents
FROM ellanlab_revenue_recognition
WHERE recognition_date >= CURRENT_DATE - INTERVAL '60 days'
GROUP BY recognition_date
ORDER BY recognition_date;

-- 4) Reconciliação contábil (ledger vs journal) - visão de divergência
WITH cmp AS (
  SELECT
    fl.external_reference,
    fl.amount_cents AS ledger_amount_cents,
    COALESCE((
      SELECT SUM(jel.debit_amount)
      FROM journal_entry_lines jel
      JOIN journal_entries je2 ON je2.id = jel.journal_entry_id
      WHERE je2.dedupe_key = fl.external_reference
    ), 0) AS journal_debit_total
  FROM financial_ledger fl
)
SELECT
  external_reference,
  ledger_amount_cents,
  CAST(ROUND(journal_debit_total * 100) AS BIGINT) AS journal_amount_cents_derived
FROM cmp
WHERE ledger_amount_cents <> CAST(ROUND(journal_debit_total * 100) AS BIGINT)
ORDER BY external_reference DESC
LIMIT 200;
