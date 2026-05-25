const BASE = import.meta.env.VITE_SECURITY_API_BASE || "/api/v1/security";

function headers(token) {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function securityFetch(path, { method = "GET", token, body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: headers(token),
    ...(body != null ? { body: JSON.stringify(body) } : {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return data;
}

export const securityCrudApi = {
  seed: (token) => securityFetch("/seed", { method: "POST", token }),
  listUsers: (token) => securityFetch("/users", { token }),
  getUser: (token, id) => securityFetch(`/users/${encodeURIComponent(id)}`, { token }),
  createUser: (token, body) => securityFetch("/users", { method: "POST", token, body }),
  updateUser: (token, id, body) => securityFetch(`/users/${encodeURIComponent(id)}`, { method: "PATCH", token, body }),
  deleteUser: (token, id) => securityFetch(`/users/${encodeURIComponent(id)}`, { method: "DELETE", token }),
  listRoles: (token, userId) =>
    securityFetch(userId ? `/roles?user_id=${encodeURIComponent(userId)}` : "/roles", { token }),
  getRole: (token, id) => securityFetch(`/roles/${encodeURIComponent(id)}`, { token }),
  createRole: (token, body) => securityFetch("/roles", { method: "POST", token, body }),
  updateRole: (token, id, body) => securityFetch(`/roles/${encodeURIComponent(id)}`, { method: "PATCH", token, body }),
  deleteRole: (token, id) => securityFetch(`/roles/${encodeURIComponent(id)}`, { method: "DELETE", token }),
  matrix: (token) => securityFetch("/permissions/matrix", { token }),
  listApiKeys: (token, userId) =>
    securityFetch(userId ? `/api-keys?user_id=${encodeURIComponent(userId)}` : "/api-keys", { token }),
  rotateApiKey: (token, body) => securityFetch("/api-keys/rotate", { method: "POST", token, body }),
  listWebhooks: (token) => securityFetch("/webhooks", { token }),
  webhookConfig: (token, body) => securityFetch("/webhook-config", { method: "POST", token, body }),
};
