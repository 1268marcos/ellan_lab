export interface OpsAuditEvent {
  id?: string;
  action: string;
  result: "SUCCESS" | "ERROR" | "WARNING";
  order_id?: string;
  user_id?: string;
  correlation_id?: string;
  created_at?: string;
}

export interface OpsKpiSnapshot {
  total?: number;
  success?: number;
  error?: number;
  warning?: number;
}

export type OpsDomain = "checkout" | "kiosk" | "ops" | "fiscal" | "global";
