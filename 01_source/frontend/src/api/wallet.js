import { financeApi } from "./financeClient";

export const walletApi = {
  getBalance: (partnerId) =>
    financeApi.get(`/wallet/${partnerId}/balance`).catch(() => financeApi.get(`/v1/balance/${partnerId}`)),

  getTransactions: (partnerId, params) =>
    financeApi.get(`/wallet/${partnerId}/transactions`, { params }),

  getExpiredCredits: (partnerId) =>
    financeApi
      .get(`/wallet/${partnerId}/credits/expired`)
      .catch(() =>
        financeApi.get(`/v1/wallet/${partnerId}/credits/expired`).catch(() => ({ data: [] })),
      ),

  applyCredit: (partnerId, amount, orderId) =>
    financeApi
      .post(`/wallet/${partnerId}/apply-credit`, { amount, order_id: orderId })
      .catch(() =>
        financeApi.post(`/v1/credit-offer`, {
          user_id: partnerId,
          amount,
          promotional: false,
        }),
      ),

  reconcile: () => financeApi.post(`/wallet/reconcile`).catch(() => financeApi.post(`/v1/reconcile`)),

  getDivergences: () => financeApi.get(`/wallet/divergences`),

  getReconcileHistory: () => financeApi.get(`/wallet/reconcile/history`),
};
