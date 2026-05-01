import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  accountingApprovalsToCsvRows,
  buildAccountingApprovalsCsv,
  fetchAccountingApprovalsCompare,
  fetchAccountingApprovalsDivergenceHealth,
  fetchConsolidatedAccountingApprovals,
  postAccountingApprovalsRetention,
} from "./fiscalAccountingApprovalsHistory";

function jsonResponse(ok, body) {
  return {
    ok,
    json: async () => body,
  };
}

describe("accountingApprovalsToCsvRows", () => {
  it("mapeia itens com payload_json.approval para colunas CSV", () => {
    const { headers, rows } = accountingApprovalsToCsvRows([
      {
        id: "a1",
        owner: "ops",
        status: "PENDING_REVIEW",
        eta: "D+1",
        created_at: "2026-05-01T10:00:00Z",
        payload_json: { approval: { notes: "linha1\nlinha2" } },
      },
    ]);
    expect(headers).toEqual(["id", "owner", "status", "eta", "created_at", "approval_notes_preview"]);
    expect(rows).toHaveLength(1);
    expect(rows[0][0]).toBe("a1");
    expect(rows[0][5]).toContain("linha1 linha2");
    expect(rows[0][5]).not.toContain("\n");
  });

  it("aceita lista vazia e campos em falta", () => {
    const { headers, rows } = accountingApprovalsToCsvRows([]);
    expect(headers.length).toBe(6);
    expect(rows).toEqual([]);
    const { rows: r2 } = accountingApprovalsToCsvRows([{}]);
    expect(r2[0].every((cell) => cell === "")).toBe(true);
  });
});

describe("buildAccountingApprovalsCsv", () => {
  it("gera CSV com escape de aspas", () => {
    const csv = buildAccountingApprovalsCsv({
      headers: ["a", "b"],
      rows: [
        ["ok", 'say "hi"'],
        ["x", "y"],
      ],
    });
    expect(csv).toBe('a,b\n"ok","say ""hi"""\n"x","y"');
  });
});

describe("fetchConsolidatedAccountingApprovals (mock fetch)", () => {
  let fetchSpy;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });
  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("agrega páginas até offset >= total", async () => {
    fetchSpy
      .mockResolvedValueOnce(jsonResponse(true, { items: [{ id: "a" }, { id: "b" }], total: 5 }))
      .mockResolvedValueOnce(jsonResponse(true, { items: [{ id: "c" }, { id: "d" }], total: 5 }))
      .mockResolvedValueOnce(jsonResponse(true, { items: [{ id: "e" }], total: 5 }));

    const out = await fetchConsolidatedAccountingApprovals({
      billingBase: "http://billing.test",
      getHeaders: () => ({ "X-Token": "t" }),
      pageSize: 2,
    });
    expect(out.items).toHaveLength(5);
    expect(out.total).toBe(5);
    expect(fetchSpy).toHaveBeenCalledTimes(3);
    const firstUrl = fetchSpy.mock.calls[0][0];
    expect(String(firstUrl)).toContain("limit=2");
    expect(String(firstUrl)).toContain("offset=0");
    expect(String(fetchSpy.mock.calls[1][0])).toContain("offset=2");
    expect(String(fetchSpy.mock.calls[2][0])).toContain("offset=4");
  });

  it("propaga filtros na query string", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { items: [], total: 0 }));
    await fetchConsolidatedAccountingApprovals({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      filters: { owner: "  o1  ", status: "OK", date_from: "2026-01-01", date_to: "2026-01-31" },
    });
    const url = String(fetchSpy.mock.calls[0][0]);
    expect(url).toContain("owner=o1");
    expect(url).toContain("status=OK");
    expect(url).toContain("date_from=2026-01-01");
    expect(url).toContain("date_to=2026-01-31");
  });

  it("clampa pageSize ao intervalo 1–500", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { items: [], total: 0 }));
    await fetchConsolidatedAccountingApprovals({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      pageSize: 9999,
    });
    expect(String(fetchSpy.mock.calls[0][0])).toContain("limit=500");

    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { items: [], total: 0 }));
    await fetchConsolidatedAccountingApprovals({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      pageSize: 0,
    });
    expect(String(fetchSpy.mock.calls[1][0])).toContain("limit=1");
  });

  it("lança com mensagem do backend quando !ok", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(false, { detail: "token inválido" }));
    await expect(
      fetchConsolidatedAccountingApprovals({
        billingBase: "http://billing.test",
        getHeaders: () => ({}),
      }),
    ).rejects.toThrow(/token inválido/);
  });
});

describe("fetchAccountingApprovalsCompare / divergence-health / retention (mock fetch)", () => {
  let fetchSpy;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });
  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("fetchAccountingApprovalsCompare monta query e devolve JSON", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { diff: [] }));
    const data = await fetchAccountingApprovalsCompare({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      currentId: "c1",
      previousId: "p9",
    });
    expect(data).toEqual({ diff: [] });
    const url = String(fetchSpy.mock.calls[0][0]);
    expect(url).toContain("/admin/fiscal/accounting-approvals/compare");
    expect(url).toContain("current_id=c1");
    expect(url).toContain("previous_id=p9");
  });

  it("fetchAccountingApprovalsDivergenceHealth clampa window e prolonged_edges", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { ok: true }));
    await fetchAccountingApprovalsDivergenceHealth({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      window: 1,
      prolongedEdges: 1,
    });
    const url = String(fetchSpy.mock.calls[0][0]);
    expect(url).toContain("window=3");
    expect(url).toContain("prolonged_edges=2");
  });

  it("postAccountingApprovalsRetention envia POST JSON", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, { applied: true }));
    const out = await postAccountingApprovalsRetention({
      billingBase: "http://billing.test",
      getHeaders: () => ({ "X-Internal": "1" }),
      body: { max_rows: 100 },
    });
    expect(out).toEqual({ applied: true });
    expect(fetchSpy.mock.calls[0][1].method).toBe("POST");
    expect(fetchSpy.mock.calls[0][1].body).toBe(JSON.stringify({ max_rows: 100 }));
  });

  it("postAccountingApprovalsRetention serializa {} quando body não é objeto", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(true, {}));
    await postAccountingApprovalsRetention({
      billingBase: "http://billing.test",
      getHeaders: () => ({}),
      body: null,
    });
    expect(fetchSpy.mock.calls[0][1].body).toBe("{}");
  });

  it("fetchAccountingApprovalsCompare propaga erro quando !ok", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(false, { detail: "snapshots incompatíveis" }));
    await expect(
      fetchAccountingApprovalsCompare({
        billingBase: "http://billing.test",
        getHeaders: () => ({}),
        currentId: "a",
        previousId: "b",
      }),
    ).rejects.toThrow(/snapshots incompatíveis/);
  });

  it("fetchAccountingApprovalsDivergenceHealth propaga erro quando !ok", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(false, { detail: "serviço indisponível" }));
    await expect(
      fetchAccountingApprovalsDivergenceHealth({
        billingBase: "http://billing.test",
        getHeaders: () => ({}),
      }),
    ).rejects.toThrow(/serviço indisponível/);
  });

  it("postAccountingApprovalsRetention propaga erro quando !ok", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(false, { detail: "política rejeitada" }));
    await expect(
      postAccountingApprovalsRetention({
        billingBase: "http://billing.test",
        getHeaders: () => ({}),
        body: {},
      }),
    ).rejects.toThrow(/política rejeitada/);
  });
});
