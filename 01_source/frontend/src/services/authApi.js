// 01_source/frontend/src/services/authApi.js

const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

async function parseJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : typeof detail?.message === "string"
          ? detail.message
          : data?.message || "Erro na requisição";
    throw new Error(message);
  }
  return data;
}

export async function registerPublicUser(payload) {
  const response = await fetch(`${API_BASE}/public/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function loginPublicUser(payload) {
  const response = await fetch(`${API_BASE}/public/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function fetchPublicMe(token) {
  const response = await fetch(`${API_BASE}/public/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });
  return parseJson(response);
}

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };
}

export async function changePublicPassword(token, payload) {
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

export async function resendPublicEmailVerification(token) {
  const response = await fetch(`${API_BASE}/public/auth/email-verification/resend`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return parseJson(response);
}

export async function confirmPublicEmailVerification(token) {
  const params = new URLSearchParams({ token: String(token || "") });
  const response = await fetch(`${API_BASE}/public/auth/email-verification/confirm?${params.toString()}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  return parseJson(response);
}