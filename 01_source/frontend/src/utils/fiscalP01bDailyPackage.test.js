import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { appendP01bSignedZipEntries, buildP01bPartnerReconciliationSlice } from "./fiscalP01bDailyPackage";

const strToU8 = (s) => new TextEncoder().encode(s);
const u8ToJson = (u8) => JSON.parse(new TextDecoder().decode(u8));

async function buildSignedPayloadMock(payload) {
  return { ...payload, _signed: true };
}

describe("buildP01bPartnerReconciliationSlice", () => {
  const iso = "2026-05-04T12:00:00.000Z";

  it("lista partners vazia e d11_cross_check null sem handoff D11", () => {
    const out = buildP01bPartnerReconciliationSlice({
      e2ePayload: { items: [], decision: "NO_GO", coverage: { total: 0 } },
      d11Handoff: null,
      generatedAt: iso,
      source: "fiscal/management-daily",
    });
    expect(out.scope).toBe("SPRINT3_P0_1B_PARTNER_RECONCILIATION_SLICE");
    expect(out.partners).toEqual([]);
    expect(out.d11_cross_check).toBeNull();
    expect(out.mandatory_trace_keys).toEqual(["order_id", "invoice_id", "partner_id", "batch_id"]);
    expect(out.e2e_coverage_ref.decision).toBe("NO_GO");
  });

  it("agrega por partner_id, severidades e batches", () => {
    const out = buildP01bPartnerReconciliationSlice({
      e2ePayload: {
        items: [
          {
            severity: "ERROR",
            trace: { partner_id: "p1", batch_id: "b1", order_id: "o1", invoice_id: "i1" },
            trace_quality: { materialized_complete: true, raw_complete: false },
          },
          {
            severity: "WARN",
            trace: { partner_id: "p1", batch_id: "b2", order_id: "o2", invoice_id: "i2" },
            trace_quality: { materialized_complete: false, raw_complete: true },
          },
          { severity: "INFO", trace: { partner_id: "p2" }, trace_quality: {} },
        ],
        decision: "GO",
        coverage: { materialized_rate: 0.5, raw_rate: 0.4, total: 3 },
        handoff_evidence: { evidence_id: "e1" },
      },
      d11Handoff: {
        summary: { unique_partners: 2, unique_batches: 4, total_items: 10 },
      },
      generatedAt: iso,
      source: "fiscal/management-daily",
    });
    expect(out.partners).toHaveLength(2);
    expect(out.partners[0].partner_id).toBe("p1");
    expect(out.partners[0].gap_rows).toBe(2);
    expect(out.partners[0].severities.ERROR).toBe(1);
    expect(out.partners[0].severities.WARN).toBe(1);
    expect(out.partners[0].materialized_complete).toBe(1);
    expect(out.partners[0].raw_complete).toBe(1);
    expect(out.partners[0].batches).toEqual(["b1", "b2"]);
    expect(out.d11_cross_check).not.toBeNull();
    expect(out.d11_cross_check.storage_total_items).toBe(10);
    expect(out.d11_cross_check.e2e_distinct_partners).toBe(2);
    expect(out.e2e_coverage_ref.handoff_evidence_id).toBe("e1");
  });

  it("trunca batches por parceiro acima de 80", () => {
    const items = Array.from({ length: 85 }, (_, i) => ({
      severity: "ERROR",
      trace: { partner_id: "big", batch_id: `batch-${i}`, order_id: `o${i}`, invoice_id: `i${i}` },
      trace_quality: {},
    }));
    const out = buildP01bPartnerReconciliationSlice({
      e2ePayload: { items },
      d11Handoff: null,
      generatedAt: iso,
      source: "x",
    });
    expect(out.partners).toHaveLength(1);
    expect(out.partners[0].batches).toHaveLength(80);
    expect(out.partners[0].batches_truncated).toBe(true);
  });
});

describe("appendP01bSignedZipEntries", () => {
  const ts = "ts-fix";
  const nowIso = "2026-05-04T14:00:00.000Z";
  const baseOpts = {
    billingBase: "http://billing.lab/",
    getHeaders: () => ({ "X-Internal": "t" }),
    buildSignedPayload: buildSignedPayloadMock,
    strToU8,
    fileBasePrefix: "ELLAN_FISCAL_DAILY",
    ts,
    nowIso,
    d11Handoff: null,
    source: "fiscal/management-daily",
  };

  let fetchSpy;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });
  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("pedido GET usa base sem barra final e limit codificado", async () => {
    fetchSpy.mockResolvedValueOnce({ ok: true, json: async () => ({ items: [] }) });
    await appendP01bSignedZipEntries({ ...baseOpts, zipEntries: {}, e2eLimit: 120 });
    const url = String(fetchSpy.mock.calls[0][0]);
    expect(url.startsWith("http://billing.lab/admin/fiscal/global/sprint3/e2e-audit-trail")).toBe(true);
    expect(url).toContain("status=OPEN");
    expect(url).toContain("limit=120");
  });

  it("falha de rede grava P0_1B_E2E_AUDIT_ERROR com scope attach", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("ECONNREFUSED"));
    const zipEntries = {};
    await appendP01bSignedZipEntries({ ...baseOpts, zipEntries });
    const key = Object.keys(zipEntries).find((k) => k.includes("P0_1B_E2E_AUDIT_ERROR"));
    expect(key).toBeDefined();
    const body = u8ToJson(zipEntries[key]);
    expect(body.scope).toBe("SPRINT3_P0_1B_E2E_ATTACH_ERROR");
    expect(String(body.error)).toMatch(/ECONNREFUSED/);
  });

  it("HTTP !ok grava http_status e detail", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 503,
      json: async () => ({ detail: "overload" }),
    });
    const zipEntries = {};
    await appendP01bSignedZipEntries({ ...baseOpts, zipEntries });
    const key = Object.keys(zipEntries).find((k) => k.includes("P0_1B_E2E_AUDIT_ERROR"));
    const body = u8ToJson(zipEntries[key]);
    expect(body.http_status).toBe(503);
    expect(body.error).toBe("overload");
  });

  it("sucesso grava E2E audit trail assinado e slice P0-1b por parceiro", async () => {
    const e2ePayload = {
      items: [{ severity: "ERROR", trace: { partner_id: "px", order_id: "o", invoice_id: "i", batch_id: "b" } }],
      decision: "GO",
    };
    fetchSpy.mockResolvedValueOnce({ ok: true, json: async () => e2ePayload });
    const zipEntries = {};
    await appendP01bSignedZipEntries({ ...baseOpts, zipEntries });
    const keys = Object.keys(zipEntries);
    expect(keys.some((k) => k.includes("SPRINT3_E2E_AUDIT_TRAIL"))).toBe(true);
    expect(keys.some((k) => k.includes("P0_1B_PARTNER_RECONCILIATION"))).toBe(true);
    const e2eKey = keys.find((k) => k.includes("SPRINT3_E2E_AUDIT_TRAIL"));
    const e2eBody = u8ToJson(zipEntries[e2eKey]);
    expect(e2eBody._signed).toBe(true);
    expect(e2eBody.items).toHaveLength(1);
    const sliceKey = keys.find((k) => k.includes("P0_1B_PARTNER_RECONCILIATION"));
    const sliceBody = u8ToJson(zipEntries[sliceKey]);
    expect(sliceBody.scope).toBe("SPRINT3_P0_1B_PARTNER_RECONCILIATION_SLICE");
    expect(sliceBody._signed).toBe(true);
    expect(sliceBody.partners[0].partner_id).toBe("px");
  });
});
