-- 001_market_ticks_ready.sql
-- Pacote separado "market-data ready" (não faz parte do backlog fiscal FA-5).
-- Objetivo: ingestão de ticks/trades com TimescaleDB + OHLCV.

-- Pré-requisitos:
-- 1) extensão timescaledb instalada no OS/imagem e ativa no DB:
--    CREATE EXTENSION IF NOT EXISTS timescaledb;
-- 2) opcional para UUID no banco:
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Tabela base (ticks/trades)
CREATE TABLE IF NOT EXISTS market_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price NUMERIC(12,4) NOT NULL,
    volume BIGINT,
    side TEXT CHECK (side IN ('BUY', 'SELL')),
    exchange TEXT,
    trade_id UUID NOT NULL DEFAULT gen_random_uuid(),
    PRIMARY KEY (time, trade_id)
);

-- 2) Hypertable (chunk diário)
SELECT create_hypertable(
    'market_ticks',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    create_default_indexes => FALSE,
    if_not_exists => TRUE
);

-- 3) Índices para consultas operacionais/BI
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON market_ticks (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_exchange ON market_ticks (exchange) WHERE exchange IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ticks_trade_id ON market_ticks (trade_id);

-- 4) Compressão columnar
ALTER TABLE market_ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('market_ticks', INTERVAL '7 days', if_not_exists => TRUE);

-- 5) Retenção de dados brutos
SELECT add_retention_policy('market_ticks', INTERVAL '2 years', if_not_exists => TRUE);

-- 6) Continuous Aggregate OHLCV de 1 hora
CREATE MATERIALIZED VIEW IF NOT EXISTS candle_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    symbol,
    FIRST(price, time) AS open,
    MAX(price) AS high,
    MIN(price) AS low,
    LAST(price, time) AS close,
    COALESCE(SUM(volume), 0) AS total_volume,
    COUNT(*) AS trade_count
FROM market_ticks
GROUP BY bucket, symbol
WITH NO DATA;

-- 7) Refresh automático da CAGG
SELECT add_continuous_aggregate_policy(
    'candle_1h',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '0',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE
);
