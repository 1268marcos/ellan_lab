-- ml_predictor_service: refresh MV + upsert rolling 70d into ml_features_daily.
-- Run after migrations; requires UNIQUE index on ml_features_daily_mv (locker_id, feature_date).

ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS temperature_avg_70d numeric(10,4);
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS humidity_avg_70d numeric(10,4);
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS battery_min_70d numeric(10,2);
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS door_failures_70d integer NOT NULL DEFAULT 0;
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS usage_events_70d integer NOT NULL DEFAULT 0;
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS uptime_hours_70d numeric(10,6);
ALTER TABLE public.ml_features_daily ADD COLUMN IF NOT EXISTS failure_label_70d smallint NOT NULL DEFAULT 0;

-- CONCURRENTLY needs a unique index without WHERE (see schema: uq_ml_features_daily_mv_locker_date).
REFRESH MATERIALIZED VIEW CONCURRENTLY public.ml_features_daily_mv;

CREATE OR REPLACE FUNCTION public.refresh_ml_features_daily_70d(p_from date, p_to date)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE n bigint;
BEGIN
  IF p_from > p_to THEN
    RAISE EXCEPTION 'p_from must be <= p_to';
  END IF;
  WITH daily AS (
    SELECT
      t.locker_id,
      (date_trunc('day', t.occurred_at AT TIME ZONE 'UTC'))::date AS d,
      avg(t.temperature_celsius)::numeric(10,4) AS temperature_mean,
      avg(t.humidity_pct)::numeric(10,4) AS humidity_mean,
      min(t.battery_pct)::numeric(10,2) AS battery_min,
      count(*)::numeric AS tel_pts,
      count(*) FILTER (WHERE t.event_type = 'DOOR_ERROR')::integer AS door_err_day,
      count(*) FILTER (WHERE t.event_type = 'DOOR_OPEN')::integer AS usage_day,
      max(CASE WHEN t.event_type = 'DOOR_ERROR' THEN 1::smallint ELSE 0::smallint END) AS fail_day
    FROM public.locker_telemetry t
    INNER JOIN public.lockers l
      ON l.id = t.locker_id
     AND l.machine_id IS NOT NULL
     AND btrim(l.machine_id::text) <> ''
    WHERE (t.occurred_at AT TIME ZONE 'UTC')::date BETWEEN p_from - 69 AND p_to
    GROUP BY t.locker_id, (date_trunc('day', t.occurred_at AT TIME ZONE 'UTC'))::date
  ),
  rolled AS (
    SELECT
      d.locker_id,
      d.d AS feature_date,
      d.temperature_mean,
      d.humidity_mean,
      d.battery_min,
      d.fail_day AS failure_label_7d,
      avg(d.temperature_mean) OVER w70 AS temperature_avg_70d,
      avg(d.humidity_mean) OVER w70 AS humidity_avg_70d,
      min(d.battery_min) OVER w70 AS battery_min_70d,
      sum(d.door_err_day) OVER w70 AS door_failures_70d,
      sum(d.usage_day) OVER w70 AS usage_events_70d,
      least(
        1::numeric,
        sum(d.tel_pts) OVER w70 / nullif(70::numeric * 288::numeric, 0)
      ) AS uptime_hours_70d,
      max(d.fail_day::integer) OVER w70 AS failure_label_70d
    FROM daily d
    WINDOW w70 AS (
      PARTITION BY d.locker_id
      ORDER BY d.d
      RANGE BETWEEN INTERVAL '69 days' PRECEDING AND CURRENT ROW
    )
  )
  INSERT INTO public.ml_features_daily (
    locker_id, feature_date,
    temperature_mean, humidity_mean, battery_min,
    door_failures_7d, usage_events_7d, uptime_hours_7d, failure_label_7d,
    temperature_avg_70d, humidity_avg_70d, battery_min_70d,
    door_failures_70d, usage_events_70d, uptime_hours_70d, failure_label_70d
  )
  SELECT
    r.locker_id,
    r.feature_date,
    r.temperature_mean,
    r.humidity_mean,
    r.battery_min,
    coalesce(mv.door_failures_7d, 0),
    coalesce(mv.usage_events_7d, 0),
    coalesce(mv.uptime_hours_7d, 0),
    coalesce(r.failure_label_7d, 0::smallint),
    r.temperature_avg_70d,
    r.humidity_avg_70d,
    r.battery_min_70d,
    r.door_failures_70d::integer,
    r.usage_events_70d::integer,
    r.uptime_hours_70d,
    r.failure_label_70d::smallint
  FROM rolled r
  LEFT JOIN public.ml_features_daily_mv mv
    ON mv.locker_id = r.locker_id AND mv.feature_date = r.feature_date
  WHERE r.feature_date BETWEEN p_from AND p_to
  ON CONFLICT (locker_id, feature_date) DO UPDATE SET
    temperature_mean = excluded.temperature_mean,
    humidity_mean = excluded.humidity_mean,
    battery_min = excluded.battery_min,
    door_failures_7d = excluded.door_failures_7d,
    usage_events_7d = excluded.usage_events_7d,
    uptime_hours_7d = excluded.uptime_hours_7d,
    failure_label_7d = excluded.failure_label_7d,
    temperature_avg_70d = excluded.temperature_avg_70d,
    humidity_avg_70d = excluded.humidity_avg_70d,
    battery_min_70d = excluded.battery_min_70d,
    door_failures_70d = excluded.door_failures_70d,
    usage_events_70d = excluded.usage_events_70d,
    uptime_hours_70d = excluded.uptime_hours_70d,
    failure_label_70d = excluded.failure_label_70d;

  GET DIAGNOSTICS n = ROW_COUNT;
  RETURN n;
END;
$$;
