import { describe, expect, it } from "vitest";
import { buildD11OrderIdRollupFromGapRows } from "./fiscalD11OrderIdRollup";

describe("buildD11OrderIdRollupFromGapRows", () => {
  it("ignora linhas sem order_id e agrega severidades", () => {
    const rollup = buildD11OrderIdRollupFromGapRows([
      { order_id: "ord-1", severity: "ERROR", gap_type: "PAID_WITHOUT_INVOICE" },
      { order_id: "ord-1", severity: "WARN", gap_type: "ISSUED_WITHOUT_PAID" },
      { order_id: "", severity: "ERROR", gap_type: "X" },
      { order_id: "ord-2", severity: "INFO", gap_type: "PAID_WITHOUT_INVOICE" },
    ]);
    expect(rollup.scope).toBe("SPRINT2_D11_ORDER_ID_ROLLUP");
    expect(rollup.source_rows).toBe(4);
    expect(rollup.unique_orders_with_gaps).toBe(2);
    expect(rollup.orders[0].order_id).toBe("ord-1");
    expect(rollup.orders[0].gap_count).toBe(2);
    expect(rollup.orders[0].by_severity.ERROR).toBe(1);
    expect(rollup.orders[0].by_severity.WARN).toBe(1);
    expect(rollup.orders[1].order_id).toBe("ord-2");
  });

  it("retorna lista vazia quando não há pedidos", () => {
    const rollup = buildD11OrderIdRollupFromGapRows([]);
    expect(rollup.unique_orders_with_gaps).toBe(0);
    expect(rollup.orders).toEqual([]);
  });
});
