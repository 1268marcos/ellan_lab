import { api } from './client'

/** GET /intelligence/at-risk */
export type AtRiskRow = {
  locker_id: string
  health_score: number | null
  failure_probability: number | null
  battery_min: number | null
  door_failures_70d: number | null
  last_prediction_at: string | null
  region: string | null
  operator_id: string | null
}

export type AtRiskResponse = {
  rows: AtRiskRow[]
  page: number
  page_size: number
  total: number
}

export type GetAtRiskParams = {
  partner_id?: string
  page?: number
  page_size?: number
  health_max?: number
  region?: string
  operator_id?: string
}

/** GET /ml/predict/{locker_id} */
export type MlPredictResponse = {
  locker_id: string
  failure_probability: number
  health_score: number
  model_version: string
}

/** GET /ops/lockers/{locker_id}/occupancy-forecast */
export type OccupancyForecastHour = {
  hour_start: string
  occupied_slots_fraction: number
  occupied_pct_slots: number
  occupied_slots_est: number
  slots_total: number
}

export type OccupancyAlert = {
  from_hour_index: number | null
  to_hour_index: number | null
  hours: number
  peak_occupancy_fraction: number
}

export type OccupancyForecastResponse = {
  locker_id: string
  hours: number
  model: string
  meta: Record<string, unknown>
  forecast: OccupancyForecastHour[]
  alerts: OccupancyAlert[]
  alert_policy: {
    threshold_fraction: number
    consecutive_hours: number
    description: string
  }
}

export type GetOccupancyForecastParams = {
  partner_id?: string
  hours?: number
}

/** GET /feedback/ops-dashboard */
export type FeedbackNpsSeriesPoint = {
  d: string
  nps: number | null
  responses: number
}

export type FeedbackSentimentSeriesPoint = {
  d: string
  avg_sentiment_score: number | null
  positive_count: number
  negative_count: number
}

export type FeedbackWordCloudItem = {
  text: string
  value: number
}

export type FeedbackLdaTopic = {
  topic_id: number
  words: string[]
  weights: number[]
}

export type FeedbackLdaTopics =
  | {
      ok: true
      n_topics: number
      topics: FeedbackLdaTopic[]
    }
  | {
      ok: false
      reason?: string
      topics: FeedbackLdaTopic[]
    }

export type FeedbackRecentRow = {
  id: string
  order_id: string | null
  rating: number | null
  comment: string | null
  sentiment_score: number | null
  sentiment_label: string | null
  topics: unknown
  user_intent: string | null
  created_at: string | null
}

export type FeedbackOpsDashboardResponse =
  | {
      ok: true
      table_ready: false
      nps: null
      nps_series: []
      sentiment_series: []
      word_cloud: []
      lda_topics: { ok: false; topics: [] }
      recent: []
      negative_alerts_7d: number
    }
  | {
      ok: true
      table_ready: true
      days: number
      nps: number | null
      nps_series: FeedbackNpsSeriesPoint[]
      sentiment_series: FeedbackSentimentSeriesPoint[]
      word_cloud: FeedbackWordCloudItem[]
      lda_topics: FeedbackLdaTopics
      recent: FeedbackRecentRow[]
      negative_alerts_7d: number
    }

export type GetFeedbackDashboardParams = {
  days?: number
}

export async function getAtRisk(params?: GetAtRiskParams): Promise<AtRiskResponse> {
  const { data } = await api.get<AtRiskResponse>('/intelligence/at-risk', { params })
  return data
}

export async function predictLocker(
  lockerId: string,
  params?: { partner_id?: string },
): Promise<MlPredictResponse> {
  const { data } = await api.get<MlPredictResponse>(`/ml/predict/${encodeURIComponent(lockerId)}`, {
    params,
  })
  return data
}

export async function getOccupancyForecast(
  lockerId: string,
  params?: GetOccupancyForecastParams,
): Promise<OccupancyForecastResponse> {
  const { data } = await api.get<OccupancyForecastResponse>(
    `/ops/lockers/${encodeURIComponent(lockerId)}/occupancy-forecast`,
    { params },
  )
  return data
}

export async function getFeedbackDashboard(
  params?: GetFeedbackDashboardParams,
): Promise<FeedbackOpsDashboardResponse> {
  const { data } = await api.get<FeedbackOpsDashboardResponse>('/feedback/ops-dashboard', { params })
  return data
}

export const mlApi = {
  getAtRisk,
  predictLocker,
  getOccupancyForecast,
  getFeedbackDashboard,
}
