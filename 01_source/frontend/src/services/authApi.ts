const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

type UnknownRecord = Record<string, unknown>;

async function parseJson(response: Response): Promise<unknown> {
  const data = (await response.json().catch(() => ({}))) as UnknownRecord;
  if (!response.ok) {
    const detail = data?.detail;
    const detailFromArray = Array.isArray(detail)
      ? detail
          .map((item: unknown) => {
            if (typeof item === "string") return item;
            const row = item as UnknownRecord;
            if (typeof row?.msg === "string") return row.msg;
            return "";
          })
          .filter(Boolean)
          .join(" | ")
      : "";
    const message =
      typeof detail === "string"
        ? detail
        : detailFromArray
          ? detailFromArray
          : typeof (detail as UnknownRecord)?.message === "string"
            ? String((detail as UnknownRecord).message)
            : typeof data?.message === "string"
              ? String(data.message)
              : "Erro na requisição";
    throw new Error(message);
  }
  return data;
}

export async function registerPublicUser(payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function loginPublicUser(payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function requestPublicPasswordReset(payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function resetPublicPassword(payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function fetchPublicMe(token: string | null) {
  const response = await fetch(`${API_BASE}/public/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });
  return parseJson(response);
}

export async function fetchPublicRoles(token: string | null) {
  const response = await fetch(`${API_BASE}/public/auth/me/roles`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });
  return parseJson(response);
}

function authHeaders(token: string | null) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };
}

export async function changePublicPassword(token: string | null, payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/change-password`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function resendPublicEmailVerification(token: string | null) {
  const response = await fetch(`${API_BASE}/public/auth/email-verification/resend`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return parseJson(response);
}

export async function confirmPublicEmailVerification(token: unknown) {
  const params = new URLSearchParams({ token: String(token || "") });
  const response = await fetch(
    `${API_BASE}/public/auth/email-verification/confirm?${params.toString()}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
    }
  );
  return parseJson(response);
}

export async function fetchPublicAuthorizationPolicy() {
  const response = await fetch(`${API_BASE}/public/auth/authorization-policy`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  return parseJson(response);
}

export async function upsertPublicFiscalProfile(token: string | null, payload: unknown) {
  const response = await fetch(`${API_BASE}/public/auth/me/fiscal-profile`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}
