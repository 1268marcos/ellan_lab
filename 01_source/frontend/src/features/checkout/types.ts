export type CheckoutChannel = "ONLINE" | "KIOSK";

export interface CheckoutCurrentOrder {
  order_id: string;
  channel: CheckoutChannel;
  status: string;
  amount_cents: number;
  currency: string;
  region: string;
  allocation_id?: string | null;
  slot?: number | null;
  pickup_id?: string;
  manual_code?: string;
}

export interface CheckoutPaymentResponse {
  status: "success" | "pending" | "failed" | "simulated" | "idle";
  message?: string;
  transaction_id?: string;
  raw?: Record<string, unknown>;
}

export interface CheckoutPickupResponse {
  status: "success" | "failed" | "idle";
  pickup_id?: string;
  manual_code?: string;
  raw?: Record<string, unknown>;
}
