export type KioskFlowStatus =
  | "IDLE"
  | "SELECTING_ITEMS"
  | "PAYMENT_PENDING"
  | "PAYMENT_CONFIRMED"
  | "DISPENSING"
  | "COMPLETED"
  | "ERROR";

export interface KioskSessionContext {
  kiosk_id: string;
  session_id?: string;
  locale?: string;
  currency?: string;
}

export interface KioskOrderSnapshot {
  order_id: string;
  status: KioskFlowStatus;
  totem_id?: string;
  slot?: number | null;
  amount_cents?: number;
}
