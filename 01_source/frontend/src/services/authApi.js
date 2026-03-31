// 01_source/frontend/src/services/authApi.js

const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

async function parseJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.detail || "Erro na requisição";
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