import axios from "axios";

/** Proxy dev: vite → wallet-service (ver `vite.config.js` `/api/wallet-svc`). */
export const financeApi = axios.create({
  baseURL: "/api/wallet-svc",
  timeout: 15_000,
});

financeApi.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? "request failed";
    console.error("[financeApi]", err.response?.status, msg);
    return Promise.reject(err);
  },
);
