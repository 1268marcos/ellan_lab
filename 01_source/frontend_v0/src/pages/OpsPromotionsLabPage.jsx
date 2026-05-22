
import React, { useCallback, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  criticalBannerStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  opsSanityCardStyle,
  summary24hHintStyle,
  tableStyle,
  tdStyle,
  thStyle,
} from "../styles/opsShellStyles";

function formatMoney(cents) {
  const n = Number(cents);
  if (Number.isNaN(n)) return "—";
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n / 100);
  } catch {
    return `${(n / 100).toFixed(2)}`;
  }
}

function WorkspaceCard({ title, hint, children }) {
  return (
    <section style={{ ...opsSanityCardStyle, marginTop: 10 }}>
      <h3 style={{ margin: "0 0 6px", fontSize: 14 }}>{title}</h3>
      {hint ? <p style={{ ...summary24hHintStyle, margin: "0 0 10px" }}>{hint}</p> : null}
      {children}
    </section>
  );
}

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const FEATURED = ["INPOST", "MAGALU", "MERCADO_LIVRE", "CORREIOS", "AMAZON_HUB", "DHL_PACKSTATION"];

export default function OpsPromotionsLabPage({ embedded = false }) {
  const { token } = useAuth();
  const headers = token ? { Accept: "application/json", "Content-Type": "application/json", Authorization: `Bearer ${token}` } : {};

  const [promoCode, setPromoCode] = useState("MAGALU10");
  const [orderId, setOrderId] = useState("LAB-PREVIEW-001");
  const [totalCents, setTotalCents] = useState("10000");
  const [player, setPlayer] = useState("MAGALU");
  const [country, setCountry] = useState("BR");
  const [simulateResult, setSimulateResult] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [conflicts, setConflicts] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  const run = useCallback(
    async (path, body) => {
      setLoading(path);
      setError("");
      try {
        const r = await fetch(`${BASE}${path}`, {
          method: body ? "POST" : "GET",
          headers,
          body: body ? JSON.stringify(body) : undefined,
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j?.detail?.message || j?.detail || "Falha na API");
        return j;
      } catch (e) {
        setError(String(e?.message || e));
        return null;
      } finally {
        setLoading("");
      }
    },
    [headers],
  );

  const onSimulate = () =>
    void run("/promotions/simulate", {
      promotion_code: promoCode.trim(),
      order_id: orderId.trim(),
      total_amount_cents: Number(totalCents) || 0,
      player_code: player.trim() || null,
      country_code: country.trim() || null,
    }).then((j) => j && setSimulateResult(j));

  const onMatch = () =>
    void run("/promotions/match", {
      total_amount_cents: Number(totalCents) || 0,
      player_code: player.trim() || null,
      country_code: country.trim() || null,
      limit: 15,
    }).then((j) => j && setMatchResult(j));

  const onConflicts = () => void run("/promotions/conflicts").then((j) => j && setConflicts(j));

  const onMatrix = () => void run("/promotions/player-matrix").then((j) => j && setMatrix(j));

  const inputStyle = healthLocalFilterInputStyle;
  const labelStyle = healthLocalFilterFieldStyle;

  return (
    <div className={embedded ? "space-y-4" : ""}>
      <WorkspaceCard
        title="Laboratório de promoções"
        hint="Simule desconto (dry-run), descubra promoções elegíveis, conflitos de escopo e matriz player — sem gravar resgate."
      >
        <div style={healthLocalFilterRowStyle}>
          <label style={labelStyle}>
            Código promoção
            <input value={promoCode} onChange={(e) => setPromoCode(e.target.value)} style={inputStyle} list="lab-promo-codes" />
          </label>
          <label style={labelStyle}>
            Pedido
            <input value={orderId} onChange={(e) => setOrderId(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Total (centavos)
            <input value={totalCents} onChange={(e) => setTotalCents(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Player
            <input value={player} onChange={(e) => setPlayer(e.target.value)} style={inputStyle} placeholder="MAGALU" />
          </label>
          <label style={labelStyle}>
            País
            <input value={country} onChange={(e) => setCountry(e.target.value)} style={inputStyle} maxLength={8} />
          </label>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
          {FEATURED.map((code) => (
            <button
              key={code}
              type="button"
              style={{ ...buttonGhostStyle, fontSize: 11, padding: "2px 8px" }}
              onClick={() => {
                setPlayer(code);
                setPromoCode(code.includes("MAGALU") ? "MAGALU10" : promoCode);
              }}
            >
              {code}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <button type="button" style={buttonPrimaryStyle} onClick={onSimulate} disabled={!!loading}>
            {loading === "/promotions/simulate" ? "…" : "Simular desconto"}
          </button>
          <button type="button" style={buttonGhostStyle} onClick={onMatch} disabled={!!loading}>
            Match elegíveis
          </button>
          <button type="button" style={buttonGhostStyle} onClick={onConflicts} disabled={!!loading}>
            Conflitos escopo
          </button>
          <button type="button" style={buttonGhostStyle} onClick={onMatrix} disabled={!!loading}>
            Matriz players
          </button>
        </div>
      </WorkspaceCard>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}

      {simulateResult ? (
        <WorkspaceCard title="Resultado simulação">
          <p style={summary24hHintStyle}>
            {simulateResult.valid ? (
              <>
                <strong>Válida</strong> — desconto {formatMoney(simulateResult.discount_cents)} · líquido{" "}
                {formatMoney(simulateResult.net_amount_cents)}
              </>
            ) : (
              <>
                <strong>Inválida</strong> — {simulateResult.reason || "sem motivo"}
              </>
            )}
          </p>
        </WorkspaceCard>
      ) : null}

      {matchResult?.items?.length ? (
        <WorkspaceCard title={`Match (${matchResult.total} promoções)`}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Código</th>
                <th style={thStyle}>Elegível</th>
                <th style={thStyle}>Desconto est.</th>
                <th style={thStyle}>Motivo</th>
              </tr>
            </thead>
            <tbody>
              {matchResult.items.map((row) => (
                <tr key={row.promotion_id}>
                  <td style={tdStyle}>
                    <code>{row.promotion_code}</code>
                  </td>
                  <td style={tdStyle}>{row.eligible ? "Sim" : "Não"}</td>
                  <td style={tdStyle}>{row.eligible ? formatMoney(row.estimated_discount_cents) : "—"}</td>
                  <td style={tdStyle}>{row.reason || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </WorkspaceCard>
      ) : null}

      {conflicts?.items?.length ? (
        <WorkspaceCard title={`Conflitos de escopo (${conflicts.total})`}>
          {conflicts.items.map((c) => (
            <div key={`${c.scope_type}:${c.scope_value}`} style={{ marginBottom: 10, fontSize: 13 }}>
              <strong>
                {c.scope_type}={c.scope_value}
              </strong>{" "}
              ({c.promotions_count} promoções) — {c.hint}
              <div style={{ marginTop: 4, color: "#94a3b8" }}>
                {(c.promotions || []).map((p) => p.code).join(", ")}
              </div>
            </div>
          ))}
        </WorkspaceCard>
      ) : null}

      {matrix?.items?.length ? (
        <WorkspaceCard title="Matriz player → promoções ativas">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {matrix.items.map((m) => (
              <span
                key={m.player_code}
                style={{
                  padding: "4px 10px",
                  borderRadius: 8,
                  border: "1px solid rgba(96,165,250,0.4)",
                  fontSize: 12,
                }}
              >
                {m.player_code}: {m.active_promotions}
              </span>
            ))}
          </div>
        </WorkspaceCard>
      ) : null}
    </div>
  );
}
