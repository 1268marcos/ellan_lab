
const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

type UnknownRecord = Record<string, unknown>;

async function parseJson(response: Response): Promise<unknown> {
  const data = (await response.json().catch(() => ({}))) as UnknownRecord;

  if (response.ok) {
    return data;
  }

  throw new Error(resolveApiErrorMessage(response, data));
}

function resolveApiErrorMessage(response: Response, data: UnknownRecord) {
  const detail = extractDetail(data);

  if (response.status === 401) {
    return "Sua sessão expirou ou não é mais válida. Entre novamente.";
  }

  if (response.status === 403) {
    if (
      detail === "EMAIL_NOT_VERIFIED" ||
      (typeof detail === "string" && detail.toLowerCase().includes("confirme seu e-mail"))
    ) {
      return "E-mail não verificado. Para criar pedidos, confirme seu e-mail em Segurança da conta.";
    }
    return "Você não tem permissão para acessar este recurso.";
  }

  if (response.status === 404) {
    return detail || "Recurso não encontrado.";
  }

  if (response.status === 409) {
    return detail || "Não foi possível concluir a operação por conflito de estado.";
  }

  if (response.status === 410) {
    return detail || "Este recurso não está mais disponível.";
  }

  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }

  return "Não foi possível concluir a solicitação.";
}

function extractDetail(data: UnknownRecord) {
  if (!data) return "";

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (data.detail && typeof data.detail === "object") {
    const d = data.detail as UnknownRecord;
    if (typeof d.message === "string") {
      return d.message;
    }
    if (typeof d.type === "string") {
      return d.type;
    }
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item: unknown) => {
        if (typeof item === "string") return item;
        const row = item as UnknownRecord;
        if (row?.msg) return String(row.msg);
        return "";
      })
      .filter(Boolean)
      .join(" | ");
  }

  if (typeof data.message === "string") {
    return data.message;
  }

  return "";
}

function buildAuthHeaders(token: string | null) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };
}

export async function fetchMyOrders(token: string | null) {
  const response = await fetch(`${API_BASE}/public/orders/`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function fetchOrderDetail(token: string | null, orderId: string) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function fetchOrderPickup(token: string | null, orderId: string) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}/pickup`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function resendOrderInvoiceEmail(token: string | null, orderId: string) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}/invoice-resend-email`, {
    method: "POST",
    headers: {
      ...buildAuthHeaders(token),
      "Content-Type": "application/json",
    },
  });
  return parseJson(response);
}

export async function fetchOrderInvoicePdf(token: string | null, orderId: string) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}/invoice-pdf`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });
  return parseJson(response);
}

export async function generateOrderInvoiceNow(token: string | null, orderId: string) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}/invoice-generate`, {
    method: "POST",
    headers: {
      ...buildAuthHeaders(token),
      "Content-Type": "application/json",
    },
  });
  return parseJson(response);
}

export async function fetchMyCredits(token: string | null) {
  const response = await fetch(`${API_BASE}/public/me/credits`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function previewCheckoutCredit(
  token: string | null,
  {
    amount_cents,
    use_credit = false,
    credit_id,
    region,
  }: {
    amount_cents?: number;
    use_credit?: boolean;
    credit_id?: string;
    region?: string;
  } = {}
) {
  const params = new URLSearchParams();
  params.set("amount_cents", String(Number(amount_cents || 0)));
  params.set("use_credit", String(Boolean(use_credit)));
  if (credit_id) {
    params.set("credit_id", String(credit_id));
  }
  if (region) {
    params.set("region", String(region).trim().toUpperCase());
  }

  const response = await fetch(`${API_BASE}/public/me/credits/checkout-preview?${params.toString()}`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

