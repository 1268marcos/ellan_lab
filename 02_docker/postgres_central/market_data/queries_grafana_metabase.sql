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
