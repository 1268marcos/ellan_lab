const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

async function parseJson(response) {
  const data = await response.json().catch(() => ({}));

  if (response.ok) {
    return data;
  }

  throw new Error(resolveApiErrorMessage(response, data));
}

function resolveApiErrorMessage(response, data) {
  const detail = extractDetail(data);

  if (response.status === 401) {
    return "Sua sessão expirou ou não é mais válida. Entre novamente.";
  }

  if (response.status === 403) {
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

function extractDetail(data) {
  if (!data) return "";

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
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

function buildAuthHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };
}

export async function fetchMyOrders(token) {
  const response = await fetch(`${API_BASE}/public/orders/`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function fetchOrderDetail(token, orderId) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}

export async function fetchOrderPickup(token, orderId) {
  const response = await fetch(`${API_BASE}/public/orders/${orderId}/pickup`, {
    method: "GET",
    headers: buildAuthHeaders(token),
  });

  return parseJson(response);
}